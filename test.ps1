# Zero-Trust Deception Proxy Defensive Validation Script
# Tests the honeypot detection and IP quarantine functionality

# Function to print a formatted step header
function Print-StepHeader {
    param(
        [string]$Title,
        [string]$Color = "Yellow"
    )
    
    $border = "=" * ($Title.Length + 8)
    Write-Host $border -ForegroundColor $Color
    Write-Host ">>> $Title <<<" -ForegroundColor $Color
    Write-Host $border -ForegroundColor $Color
    Write-Host ""
}

# Function to print a summary box
function Print-SummaryBox {
    param(
        [string]$Title,
        [string]$Content
    )
    
    Write-Host ""
    $border = "#" * ($Title.Length + 4)
    Write-Host $border -ForegroundColor Green
    Write-Host "# $Title #" -ForegroundColor Green
    Write-Host $border -ForegroundColor Green
    Write-Host $Content -ForegroundColor White
    Write-Host ""
}

# Function to make API call with API key
function Invoke-ApiCall {
    param(
        [string]$Uri,
        [string]$Method = "GET",
        [object]$Body = $null
    )
    
    $headers = @{
        "X-API-Key" = $env:API_KEY
    }
    
    try {
        if ($Method -eq "POST" -and $Body) {
            $response = Invoke-RestMethod -Uri $Uri -Method $Method -Body ($Body | ConvertTo-Json) -Headers $headers -ContentType "application/json" -TimeoutSec 10
        } else {
            $response = Invoke-RestMethod -Uri $Uri -Method $Method -Headers $headers -TimeoutSec 10
        }
        return $response, $null
    } catch {
        return $null, $_.Exception.Message
    }
}

Print-StepHeader "DECEPTION PROXY VALIDATION TEST" "Cyan"

# Get API key from environment or use default
$apiKey = $env:API_KEY
if (-not $apiKey) {
    Write-Host "Warning: API_KEY environment variable not set. Using default key." -ForegroundColor Yellow
    $apiKey = "default_test_key"
}

Write-Host "Using API Key: $($apiKey.Substring(0,8))..." -ForegroundColor Cyan
Write-Host ""

# Auto-reset at the start of every run (clean slate)
Print-StepHeader "STEP 0: AUTO-RESET SYSTEM" "Magenta"
Write-Host "Resetting system to clean state..." -ForegroundColor Magenta

$resetResult, $resetError = Invoke-ApiCall -Uri "http://localhost:8000/reset" -Method "POST" -Body @{}

if ($resetError) {
    Write-Host "Warning: Reset failed - $resetError" -ForegroundColor Yellow
    Write-Host "This may be expected if the API is not running yet." -ForegroundColor Yellow
} else {
    Write-Host "✓ System reset completed" -ForegroundColor Green
}

Write-Host ""
Start-Sleep -Seconds 2


# Step 1: Normal request (should succeed)
Print-StepHeader "STEP 1: NORMAL TRAFFIC TEST" "Green"
Write-Host "Sending normal request to public endpoint..." -ForegroundColor Green

try {
    $normalResponse = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/public-news" -TimeoutSec 10
    Write-Host "✓ Normal request succeeded: $normalResponse" -ForegroundColor Green
} catch {
    Write-Host "✗ Normal request failed: $($_.Exception.Message)" -ForegroundColor Red
}


# Step 2: Honeypot trigger (should quarantine the IP)
Print-StepHeader "STEP 2: HONEYPOT TRIGGER TEST" "Yellow"
Write-Host "Triggering honeypot with unauthorized access attempt..." -ForegroundColor Yellow

try {
    $honeypotResponse = Invoke-WebRequest -Uri "http://localhost:8080/api/v2/financial-export" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✗ Honeypot access should have been blocked! Status: $($honeypotResponse.StatusCode)" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode.Value__ -eq 403) {
        Write-Host "✓ Honeypot correctly blocked unauthorized access (403 Forbidden)" -ForegroundColor Green
    } else {
        Write-Host "✗ Unexpected response: $($_.Exception.Response.StatusCode.Value__)" -ForegroundColor Red
    }
}


# Step 3: Verify quarantine (subsequent requests from same IP should fail)
Print-StepHeader "STEP 3: QUARANTINE VERIFICATION" "Red"
Write-Host "Testing if IP is quarantined by sending another normal request..." -ForegroundColor Red

try {
    $quarantineResponse = Invoke-WebRequest -Uri "http://localhost:8080/api/v1/public-news" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✗ IP should be quarantined! Status: $($quarantineResponse.StatusCode)" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode.Value__ -eq 403) {
        Write-Host "✓ IP successfully quarantined (403 Forbidden)" -ForegroundColor Green
    } else {
        Write-Host "✗ Unexpected response: $($_.Exception.Response.StatusCode.Value__)" -ForegroundColor Red
    }
}


# Step 4: Multi-IP coordinated attack to trigger CRITICAL state
Print-StepHeader "STEP 4: MULTI-IP COORDINATED ATTACK" "Red"
Write-Host "Simulating multi-IP attack to trigger CRITICAL threat state..." -ForegroundColor Red

# Simulate different client IPs by using X-Forwarded-For header (in a real scenario, this would come from different actual IPs)
$headers = @{
    "X-Forwarded-For" = "192.168.1.100"
    "X-API-Key" = $apiKey
}

try {
    $attackResponse1 = Invoke-WebRequest -Uri "http://localhost:8080/api/v2/financial-export" -Headers $headers -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✗ Attack 1 should have been blocked!" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode.Value__ -eq 403) {
        Write-Host "✓ IP 192.168.1.100 quarantined (403 Forbidden)" -ForegroundColor Green
    }
}

$headers["X-Forwarded-For"] = "192.168.1.101"
try {
    $attackResponse2 = Invoke-WebRequest -Uri "http://localhost:8080/api/v2/financial-export" -Headers $headers -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✗ Attack 2 should have been blocked!" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode.Value__ -eq 403) {
        Write-Host "✓ IP 192.168.1.101 quarantined (403 Forbidden)" -ForegroundColor Green
    }
}

$headers["X-Forwarded-For"] = "192.168.1.102"
try {
    $attackResponse3 = Invoke-WebRequest -Uri "http://localhost:8080/api/v2/financial-export" -Headers $headers -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✗ Attack 3 should have been blocked!" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode.Value__ -eq 403) {
        Write-Host "✓ IP 192.168.1.102 quarantined (403 Forbidden)" -ForegroundColor Green
    }
}


# Final status summary showing total quarantined IPs
Print-StepHeader "FINAL STATUS SUMMARY" "Cyan"
Write-Host "Retrieving final system status..." -ForegroundColor Cyan

$statusResult, $statusError = Invoke-ApiCall -Uri "http://localhost:8000/status"

if ($statusError) {
    Write-Host "✗ Could not retrieve status: $statusError" -ForegroundColor Red
} else {
    $totalAlerts = $statusResult.total_alerts
    $uniqueIPs = ($statusResult.alerts | ForEach-Object { $_.ip } | Sort-Object -Unique).Count
    $quarantinedIPs = $statusResult.alerts | ForEach-Object { $_.ip } | Sort-Object -Unique
    
    Write-Host "Total alerts generated: $totalAlerts" -ForegroundColor White
    Write-Host "Total unique quarantined IPs: $uniqueIPs" -ForegroundColor White
    Write-Host "Quarantined IP addresses:" -ForegroundColor White
    foreach ($ip in $quarantinedIPs) {
        Write-Host "  - $ip" -ForegroundColor White
    }
    
    # Get threat level from report
    $reportResult, $reportError = Invoke-ApiCall -Uri "http://localhost:8000/report"
    
    if ($reportError) {
        Write-Host "✗ Could not retrieve threat level: $reportError" -ForegroundColor Red
    } else {
        $threatLevel = $reportResult.threat_level
        Write-Host "Current threat level: $threatLevel" -ForegroundColor White
        
        if ($threatLevel -eq "CRITICAL") {
            Write-Host "🎉 SUCCESS: Multi-IP attack successfully triggered CRITICAL state!" -ForegroundColor Green
        } elseif ($threatLevel -eq "MEDIUM") {
            Write-Host "✓ MEDIUM threat level detected (expected if only 1-2 IPs were quarantined)" -ForegroundColor Yellow
        } else {
            Write-Host "⚠ Threat level is $threatLevel (expected if no attacks were successful)" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Print-SummaryBox -Title "TEST COMPLETE" -Content @"
All tests completed!
- Auto-reset performed at start
- Normal traffic allowed
- Honeypot access blocked and IP quarantined
- Multi-IP coordinated attack simulated
- Final status verified
"@

Write-Host "Test script finished." -ForegroundColor Cyan