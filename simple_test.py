import requests
import time
import os

# Test the system functionality
print("Testing Deception Proxy System...")

# Get API key from environment
api_key = os.environ.get('API_KEY', 'default_test_key')
headers = {'X-API-Key': api_key}

print(f"Using API Key: {api_key[:8]}...")

# Test 1: Check API status
try:
    response = requests.get("http://localhost:8000/status", timeout=5)
    if response.status_code == 200:
        status_data = response.json()
        print(f"✅ API Status: OK - {status_data['total_alerts']} alerts")
    else:
        print(f"❌ API Status: {response.status_code}")
except Exception as e:
    print(f"❌ API Connection failed: {e}")

# Test 2: Check report
try:
    response = requests.get("http://localhost:8000/report", timeout=5)
    if response.status_code == 200:
        report_data = response.json()
        print(f"✅ Report: OK - Threat level: {report_data['threat_level']}")
    else:
        print(f"❌ Report: {response.status_code}")
except Exception as e:
    print(f"❌ Report failed: {e}")

# Test 3: Test normal traffic (this might fail if IP is quarantined from previous tests)
try:
    response = requests.get("http://localhost:8080/api/v1/public-news", timeout=5)
    if response.status_code == 200:
        print(f"✅ Normal traffic: OK - {response.text.strip()}")
    else:
        print(f"⚠️ Normal traffic: {response.status_code} (This might be expected if IP was previously quarantined)")
except Exception as e:
    print(f"⚠️ Normal traffic failed: {e} (This might be expected if IP was previously quarantined)")

# Test 4: Try to trigger honeypot (will result in quarantine for this IP)
try:
    response = requests.get("http://localhost:8080/api/v2/financial-export", timeout=5)
    print(f"⚠️ Honeypot trigger: {response.status_code} (Should be 403)")
except Exception as e:
    if "403" in str(e) or "Forbidden" in str(e):
        print("✅ Honeypot correctly blocked access (403 Forbidden)")
    else:
        print(f"⚠️ Honeypot trigger failed: {e}")

# Test 5: Check status after honeypot trigger
try:
    response = requests.get("http://localhost:8000/status", timeout=5)
    if response.status_code == 200:
        status_data = response.json()
        print(f"✅ Post-attack status: OK - {status_data['total_alerts']} total alerts")
    else:
        print(f"❌ Post-attack status: {response.status_code}")
except Exception as e:
    print(f"❌ Post-attack status failed: {e}")

print("\nSystem test completed!")
print("Note: If this IP was quarantined, you may need to restart services for clean testing.")