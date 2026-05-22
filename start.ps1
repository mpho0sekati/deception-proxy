# Start all three services of ImmuniSOC-Nexus with health checks
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Display ASCII banner
@"
  _____              _   _       _   _      _   
 |_   _|__  _ __ ___| |_| | __ _| |_(_) ___| | __
   | |/ _ \| '__/ __| __| |/ _` | __| |/ __| |/ /
   | | (_) | |  \__ \ |_| | (_| | |_| | (__|   < 
   |_|\___/|_|  |___/\__|_|\__,_|\__|_|\___|_|\_\

  ImmuniSOC-Nexus
  Starting Services in Order: API → Proxy → Dashboard
"@ | Write-Host -ForegroundColor Cyan
Write-Host ""

# Function to check if a service is running on a given port
function Test-PortAvailability {
    param([int]$Port)
    
    try {
        $tcpConnection = New-Object System.Net.Sockets.TcpClient
        $tcpConnection.Connect("localhost", $Port)
        $tcpConnection.Close()
        return $true
    } catch {
        return $false
    }
}

# Function to wait for a service to be healthy
function Wait-ServiceHealth {
    param(
        [int]$Port,
        [string]$ServiceName,
        [int]$TimeoutSeconds = 30
    )
    
    Write-Host "Waiting for $ServiceName to be available on port $Port..." -ForegroundColor Yellow
    
    $timeout = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $timeout) {
        if (Test-PortAvailability -Port $Port) {
            Write-Host "✓ $ServiceName is healthy on port $Port" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 1
    }
    
    Write-Host "✗ Timeout waiting for $ServiceName on port $Port. Service may have failed to start." -ForegroundColor Red
    Write-Host "Possible fixes:" -ForegroundColor Red
    Write-Host "  - Check if another process is using port $Port" -ForegroundColor Red
    Write-Host "  - Verify Go is installed for the proxy service" -ForegroundColor Red
    Write-Host "  - Check logs in the console windows that opened" -ForegroundColor Red
    return $false
}

# Set API key environment variable if not already set
if (-not $env:API_KEY) {
    # Generate a random API key
    $env:API_KEY = [System.Web.Security.Membership]::GeneratePassword(32, 4) -replace '[^a-zA-Z0-9]', 'A'
    Write-Host "Generated API Key for this session: $($env:API_KEY.Substring(0,8))..." -ForegroundColor Yellow
}

# 1. Start the Brain API Backend
Write-Host "`nStep 1: Starting Python Brain API on Port 8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; `$env:API_KEY='$($env:API_KEY)'; Write-Host 'Starting Brain API...'; python api.py; Write-Host 'Brain API stopped. Press any key to exit.' -ForegroundColor Red; \$null = \$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')" -WorkingDirectory $root

# Wait for API to be healthy before continuing
if (-not (Wait-ServiceHealth -Port 8000 -ServiceName "Brain API")) {
    Write-Host "Cannot proceed: Brain API failed to start." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# 2. Start the ImmuniSOC-Nexus Go Proxy
Write-Host "`nStep 2: Starting ImmuniSOC-Nexus Go Proxy on Port 8080..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; `$env:BRAIN_API_URL='http://localhost:8000/alert'; `$env:API_KEY='$($env:API_KEY)'; Write-Host 'Starting Go Proxy...'; go run proxy.go; Write-Host 'Go Proxy stopped. Press any key to exit.' -ForegroundColor Red; \$null = \$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')" -WorkingDirectory $root

# Wait for Proxy to be healthy before continuing
if (-not (Wait-ServiceHealth -Port 8080 -ServiceName "ImmuniSOC-Nexus Go Proxy")) {
    Write-Host "Cannot proceed: ImmuniSOC-Nexus Go Proxy failed to start." -ForegroundColor Red
    Write-Host "Possible fixes:" -ForegroundColor Red
    Write-Host "  - Ensure Go is installed and available in your PATH" -ForegroundColor Red
    Write-Host "  - Run 'go version' to verify Go installation" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# 3. Start the SOC Dashboard
Write-Host "`nStep 3: Starting SOC Streamlit Dashboard on Port 8501..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; `$env:API_URL='http://localhost:8000'; `$env:API_KEY='$($env:API_KEY)'; Write-Host 'Starting Streamlit Dashboard...'; streamlit run dashboard.py; Write-Host 'Dashboard stopped. Press any key to exit.' -ForegroundColor Red; \$null = \$Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')" -WorkingDirectory $root

# Brief wait for dashboard to start
Start-Sleep -Seconds 3

Write-Host "`n🎉 All services started successfully!" -ForegroundColor Green
Write-Host "Brain API: http://localhost:8000" -ForegroundColor White
Write-Host "ImmuniSOC-Nexus Proxy: http://localhost:8080" -ForegroundColor White
Write-Host "Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Yellow
Write-Host "  - The Streamlit UI should open in your browser shortly" -ForegroundColor White
Write-Host "  - Remember to use the API key for write operations" -ForegroundColor White
Write-Host "  - If services fail to start, check the individual console windows" -ForegroundColor White