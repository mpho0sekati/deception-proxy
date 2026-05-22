package main

import (
	"bytes"
    "context"
    "encoding/json"
    "log"
    "net"
    "net/http"
    "net/http/httputil"
    "net/url"
    "os"
    "os/signal"
    "strings"
    "sync"
    "syscall"
    "time"
)

const (
    defaultProxyPort     = "8080"
    defaultBackendAddr   = "127.0.0.1:8081"
    defaultBrainAPIURL   = "http://localhost:8000/alert"
    defaultHoneytokenPath = "/api/v2/financial-export"
)

type DeceptionMesh struct {
    sync.RWMutex
    blockedIPs map[string]bool
}

func NewDeceptionMesh() *DeceptionMesh {
    return &DeceptionMesh{blockedIPs: make(map[string]bool)}
}

func (dm *DeceptionMesh) Block(ip string) {
    dm.Lock()
    defer dm.Unlock()
    dm.blockedIPs[ip] = true
}

func (dm *DeceptionMesh) IsBlocked(ip string) bool {
    dm.RLock()
    defer dm.RUnlock()
    return dm.blockedIPs[ip]
}

func envOrDefault(key, fallback string) string {
    if value := strings.TrimSpace(os.Getenv(key)); value != "" {
        return value
    }
    return fallback
}

// ValidateIP ensures the IP address is in a valid format
func validateIP(ip string) bool {
    // Parse the IP address
    parsedIP := net.ParseIP(ip)
    return parsedIP != nil
}

func getClientIP(r *http.Request) string {
    if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
        parts := strings.Split(xff, ",")
        if len(parts) > 0 {
            candidate := strings.TrimSpace(parts[0])
            if validateIP(candidate) {
                return candidate
            }
        }
    }

    if ip := strings.TrimSpace(r.Header.Get("X-Real-IP")); ip != "" {
        if validateIP(ip) {
            return ip
        }
    }

    host, _, err := net.SplitHostPort(r.RemoteAddr)
    if err != nil {
        return r.RemoteAddr
    }
    return host
}

var httpClient = &http.Client{Timeout: 10 * time.Second}

func sendAlert(attackerIP, brainAPIURL, brainAPIKey string) {
    // Validate IP before sending alert
    if !validateIP(attackerIP) {
        log.Printf("[ERROR] Invalid IP address provided for alert: %s", attackerIP)
        return
    }

    payload := map[string]string{
        "ip":      attackerIP,
        "trigger": "honeytoken_accessed",
    }
    jsonPayload, err := json.Marshal(payload)
    if err != nil {
        log.Printf("[ERROR] Failed to marshal alert payload: %v", err)
        return
    }

    req, err := http.NewRequest("POST", brainAPIURL, bytes.NewBuffer(jsonPayload))
    if err != nil {
        log.Printf("[ERROR] Failed to create request for Brain API: %v", err)
        return
    }

    // Add API key header if available
    if brainAPIKey != "" {
        req.Header.Set("X-API-Key", brainAPIKey)
    }

    req.Header.Set("Content-Type", "application/json")
    if brainAPIKey != "" {
        req.Header.Set("Authorization", "Bearer "+brainAPIKey)
    }

    resp, err := httpClient.Do(req)
    if err != nil {
        log.Printf("[ERROR] Failed to send alert to Brain API: %v", err)
        return
    }
    defer resp.Body.Close()

    if resp.StatusCode >= 300 {
        log.Printf("[ERROR] Brain API returned non-success status: %s", resp.Status)
        return
    }

    log.Printf("[ALERT-SENT] Alert sent for IP %s to Brain API", attackerIP)
}

func startDummyBackend(ctx context.Context, addr string) *http.Server {
    mux := http.NewServeMux()
    mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "text/plain")
        w.WriteHeader(http.StatusOK)
        _, _ = w.Write([]byte("200 OK - Standard Route"))
    })

    server := &http.Server{Addr: addr, Handler: mux}
    go func() {
        log.Printf("[Dummy Backend] Listening on %s", addr)
        if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("[Dummy Backend] Failed: %v", err)
        }
    }()

    go func() {
        <-ctx.Done()
        _ = server.Shutdown(context.Background())
    }()

    return server
}

func main() {
    proxyPort := envOrDefault("PROXY_PORT", defaultProxyPort)
    backendAddr := envOrDefault("BACKEND_ADDR", defaultBackendAddr)
    brainAPIURL := envOrDefault("BRAIN_API_URL", defaultBrainAPIURL)
    honeytokenPath := envOrDefault("HONEYTOKEN_PATH", defaultHoneytokenPath)
    brainAPIKey := envOrDefault("BRAIN_API_KEY", "")

    ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
    defer stop()

    backendCtx, backendCancel := context.WithCancel(ctx)
    defer backendCancel()
    startDummyBackend(backendCtx, backendAddr)

    targetURL, err := url.Parse("http://" + backendAddr)
    if err != nil {
        log.Fatalf("Failed to parse backend target URL: %v", err)
    }

    proxy := httputil.NewSingleHostReverseProxy(targetURL)
    proxy.Director = func(req *http.Request) {
        req.Header.Set("X-Forwarded-For", getClientIP(req))
        req.Host = targetURL.Host
        req.URL.Scheme = targetURL.Scheme
        req.URL.Host = targetURL.Host
    }

    // Add a timeout to the reverse proxy
    proxy.Transport = &http.Transport{
        Dial: (&net.Dialer{
            Timeout:   30 * time.Second,
            KeepAlive: 30 * time.Second,
        }).Dial,
        TLSHandshakeTimeout:   10 * time.Second,
        ExpectContinueTimeout: 1 * time.Second,
    }

    mesh := NewDeceptionMesh()
    handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ip := getClientIP(r)

        // Validate the client IP
        if !validateIP(ip) {
            log.Printf("[INVALID-IP] Request from invalid IP address: %s", ip)
            http.Error(w, "400 Bad Request - Invalid IP Address", http.StatusBadRequest)
            return
        }

        if mesh.IsBlocked(ip) {
            log.Printf("[BLOCK] %s blocked by quarantine path=%s", ip, r.URL.Path)
            http.Error(w, "403 Forbidden - IP Quarantined", http.StatusForbidden)
            return
        }

        if r.URL.Path == honeytokenPath {
            log.Printf("[ALERT] Honeytoken access triggered by %s", ip)
            mesh.Block(ip)
            go sendAlert(ip, brainAPIURL, brainAPIKey)
            http.Error(w, "403 Forbidden", http.StatusForbidden)
            return
        }

        log.Printf("[PROXY] Forwarding request from %s to backend path=%s", ip, r.URL.Path)
        proxy.ServeHTTP(w, r)
    })

    server := &http.Server{Addr: ":" + proxyPort, Handler: handler}
    go func() {
        log.Printf("[Neutrophil Proxy] Listening on port %s", proxyPort)
        if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("Proxy server failed: %v", err)
        }
    }()

    <-ctx.Done()
    log.Println("Shutting down Neutrophil proxy...")
    _ = server.Shutdown(context.Background())
}