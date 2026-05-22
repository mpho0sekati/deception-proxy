import os
import requests
import streamlit as st
from datetime import datetime, timedelta
import time
import random
import json

# Import st_autorefresh - this needs to be installed separately
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st.error("Please install streamlit-autorefresh: pip install streamlit-autorefresh")
    st.stop()

API_URL = os.getenv("API_URL", "http://localhost:8000")
TIMEOUT_SECONDS = 5  # Increased timeout for better reliability

# Initialize session state
if 'threat_history' not in st.session_state:
    st.session_state.threat_history = []
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = True
if 'current_threat_level' not in st.session_state:
    st.session_state.current_threat_level = "SAFE"
if 'total_alerts' not in st.session_state:
    st.session_state.total_alerts = 0
if 'quarantined_ips' not in st.session_state:
    st.session_state.quarantined_ips = []
if 'last_simulation_time' not in st.session_state:
    st.session_state.last_simulation_time = datetime.utcnow()

st.set_page_config(
    page_title="ImmuniSOC-Nexus Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def fetch_json(endpoint: str):
    url = f"{API_URL}{endpoint}"
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"Cannot connect to API at {url}. Is the service running?"
    except requests.exceptions.Timeout:
        return None, f"Request to {url} timed out after {TIMEOUT_SECONDS} seconds"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def send_alert_to_backend(ip_address, trigger_type):
    """Send an alert to the backend API"""
    api_key = os.getenv("API_KEY")
    if not api_key:
        # Try to get from session state if available
        api_key = getattr(st.session_state, 'api_key', 'default_test_key')
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    payload = {
        "ip": ip_address,
        "trigger": trigger_type
    }
    
    try:
        response = requests.post(f"{API_URL}/alert", json=payload, headers=headers, timeout=TIMEOUT_SECONDS)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Backend returned status: {response.status_code}"
    except Exception as e:
        return False, f"Error contacting backend: {str(e)}"

def simulate_threat_event(event_type, ip_address=None):
    """Simulate a threat event and send it to the backend"""
    if ip_address is None:
        ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    event_descriptions = {
        "honeytoken_access": "Unauthorized access to financial data endpoint",
        "brute_force": "Multiple failed login attempts from single IP",
        "sql_injection": "Suspicious SQL query detected in request",
        "directory_traversal": "Attempt to access restricted system directories",
        "ddos": "High volume of requests from multiple IPs",
        "malware_scan": "Malicious payload detected in request body"
    }
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    event = {
        "timestamp": timestamp,
        "ip": ip_address,
        "trigger": event_type,
        "description": event_descriptions.get(event_type, "Unknown threat detected"),
        "severity": random.choice(["LOW", "MEDIUM", "HIGH"])
    }
    
    # Send alert to backend
    success, result = send_alert_to_backend(ip_address, event_type)
    if success:
        st.success(f"Alert sent to backend: {event_type} from {ip_address}")
    else:
        st.warning(f"Could not send alert to backend: {result}")
    
    # Add to threat history
    st.session_state.threat_history.insert(0, event)
    
    # Update metrics
    st.session_state.total_alerts += 1
    if ip_address not in st.session_state.quarantined_ips:
        st.session_state.quarantined_ips.append(ip_address)
    
    # Update threat level based on severity
    if event["severity"] == "HIGH":
        if st.session_state.current_threat_level != "CRITICAL":
            st.session_state.current_threat_level = "CRITICAL"
    elif event["severity"] == "MEDIUM" and st.session_state.current_threat_level == "SAFE":
        st.session_state.current_threat_level = "MEDIUM"
    
    return event

def reset_system():
    """Reset all system metrics to initial state"""
    st.session_state.threat_history = []
    st.session_state.current_threat_level = "SAFE"
    st.session_state.total_alerts = 0
    st.session_state.quarantined_ips = []
    st.session_state.last_simulation_time = datetime.utcnow()
    
    # Send reset command to backend
    api_key = os.getenv("API_KEY")
    if api_key:
        headers = {"X-API-Key": api_key}
        try:
            response = requests.post(f"{API_URL}/reset", headers=headers, timeout=TIMEOUT_SECONDS)
            if response.status_code == 200:
                st.success("Backend system reset successfully!")
            else:
                st.warning(f"Backend reset returned status: {response.status_code}")
        except Exception as e:
            st.warning(f"Could not reset backend: {str(e)}")

# Sidebar with interactive controls
with st.sidebar:
    st.header("🎯 Cybersecurity Simulator")
    st.write("Click buttons to simulate different cyber attacks")
    
    # Different attack simulations
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚨 Honeytoken Attack", use_container_width=True):
            simulate_threat_event("honeytoken_access")
            st.success("Honeytoken access simulated!")
        
        if st.button("🔓 Brute Force", use_container_width=True):
            simulate_threat_event("brute_force")
            st.success("Brute force attack simulated!")
    
    with col2:
        if st.button("💉 SQL Injection", use_container_width=True):
            simulate_threat_event("sql_injection")
            st.success("SQL injection detected!")
        
        if st.button("📁 Dir Traversal", use_container_width=True):
            simulate_threat_event("directory_traversal")
            st.success("Directory traversal blocked!")
    
    # More complex attacks
    if st.button("⚡ DDoS Attack", use_container_width=True):
        # Simulate multiple IPs in a DDoS attack
        for _ in range(random.randint(3, 8)):
            simulate_threat_event("ddos")
        st.success("DDoS attack simulated!")
    
    if st.button("🦠 Malware Scan", use_container_width=True):
        simulate_threat_event("malware_scan")
        st.success("Malware payload blocked!")
    
    # Reset button
    if st.button("🔄 Reset System", type="secondary", use_container_width=True):
        reset_system()
        st.success("System reset to safe state!")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Enable Auto-Refresh", value=True, key="auto_refresh_sidebar")
    if auto_refresh:
        refresh_interval = st.slider("Refresh Interval (seconds)", min_value=1, max_value=30, value=5, key="refresh_slider_sidebar")
        st_autorefresh(interval=refresh_interval * 1000, key="sidebar_refresh")

# Main dashboard header
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>ImmuniSOC-Nexus Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #666;'>Advanced Deception Mesh & Threat Detection System</h3>", unsafe_allow_html=True)

# System status indicator with color coding
if st.session_state.current_threat_level == "CRITICAL":
    status_text = "CRITICAL THREAT DETECTED"
    status_color = "#D32F2F"  # Dark red
    status_style = f"<div style='background-color: {status_color}; padding: 25px; border-radius: 10px; text-align: center; font-size: 32px; font-weight: bold; color: white; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>🚨 {status_text}</div>"
elif st.session_state.current_threat_level == "MEDIUM":
    status_text = "MEDIUM THREAT DETECTED"
    status_color = "#FF8F00"  # Amber
    status_style = f"<div style='background-color: {status_color}; padding: 25px; border-radius: 10px; text-align: center; font-size: 32px; font-weight: bold; color: white; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>⚠️ {status_text}</div>"
elif st.session_state.current_threat_level == "LOW":
    status_text = "MINOR THREAT DETECTED"
    status_color = "#FFB300"  # Light amber
    status_style = f"<div style='background-color: {status_color}; padding: 25px; border-radius: 10px; text-align: center; font-size: 32px; font-weight: bold; color: white; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>🟡 {status_text}</div>"
elif st.session_state.current_threat_level == "SAFE":
    status_text = "SYSTEM SECURE"
    status_color = "#388E3C"  # Dark green
    status_style = f"<div style='background-color: {status_color}; padding: 25px; border-radius: 10px; text-align: center; font-size: 32px; font-weight: bold; color: white; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>✅ {status_text}</div>"
else:
    status_text = "MONITORING"
    status_color = "#757575"  # Gray
    status_style = f"<div style='background-color: {status_color}; padding: 25px; border-radius: 10px; text-align: center; font-size: 32px; font-weight: bold; color: white; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>🔍 {status_text}</div>"

st.markdown(status_style, unsafe_allow_html=True)

# Key metrics in cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3 style="color: #1E88E5; margin-bottom: 10px;">🛡️ Attacks Blocked</h3>
        <h2 style="color: #0D47A1; font-size: 36px; margin: 0;">{st.session_state.total_alerts}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3 style="color: #1E88E5; margin-bottom: 10px;">🔒 IPs Quarantined</h3>
        <h2 style="color: #0D47A1; font-size: 36px; margin: 0;">{len(st.session_state.quarantined_ips)}</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3 style="color: #1E88E5; margin-bottom: 10px;">📊 Threat Level</h3>
        <h2 style="color: #0D47A1; font-size: 36px; margin: 0;">{st.session_state.current_threat_level}</h2>
    </div>
    """, unsafe_allow_html=True)

# Sidebar - Emergency Crisis Copilot (Your Secret Weapon)
with st.sidebar:
    st.header("Emergency Crisis Copilot")
    st.write("Your automated response assistant")
    
    # Generate report button
    if st.button("Generate Security Report", type="secondary"):
        if report_data:
            # Save the report to a file
            report_path = "security_report_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".md"
            try:
                with open(report_path, "w") as f:
                    f.write(f"# SECURITY INCIDENT REPORT\n")
                    f.write(f"Generated at: {report_data.get('timestamp', datetime.now().isoformat())}\n\n")
                    f.write(f"## Threat Level: **{report_data.get('threat_level', 'UNKNOWN')}**\n\n")
                    f.write(f"### Summary\n{report_data.get('summary', 'No summary available.')}\n\n")
                    f.write(f"### Layman Explanation\n{report_data.get('layman_explanation', 'No explanation available.')}\n\n")
                    f.write(f"### Recommendations\n")
                    for rec in report_data.get('recommendations', []):
                        f.write(f"- {rec}\n")
                    f.write(f"\n### Quarantined IPs\n")
                    for ip in report_data.get('quarantined_ips', []):
                        f.write(f"- {ip}\n")
                
                st.success(f"Report saved as {report_path}")
                with open(report_path, "r") as f:
                    st.download_button(
                        label="Download Report",
                        data=f.read(),
                        file_name=report_path,
                        mime="text/markdown"
                    )
            except Exception as e:
                st.error(f"Error saving report: {e}")
        else:
            st.error("No report data available")
    
    # Contact information section
    st.markdown("### Emergency Contacts")
    st.write("**Local Authorities:**")
    st.write("- SAPS: 10111")
    st.write("- Emergency: 112")
    st.write("")
    st.write("**CSIRT:**")
    st.write("- SA CSIRT: csirt@gov.za")
    
    # Immediate actions checklist
    st.markdown("### Immediate Actions")
    st.write("Follow these steps if breach detected:")
    st.checkbox("Isolate affected network segments")
    st.checkbox("Preserve evidence and logs")
    st.checkbox("Notify senior management")
    st.checkbox("Contact law enforcement if needed")
    st.checkbox("Document incident details")
    
    # Reset system button
    if st.button("Reset System", type="secondary"):
        # Call the reset endpoint
        reset_url = f"{API_URL}/reset"
        api_key = os.getenv("API_KEY")
        
        if api_key:
            headers = {"X-API-Key": api_key}
            try:
                response = requests.post(reset_url, headers=headers, timeout=TIMEOUT_SECONDS)
                if response.status_code == 200:
                    st.success("System reset successfully!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Failed to reset system: {response.status_code}")
            except Exception as e:
                st.error(f"Error connecting to reset endpoint: {str(e)}")
        else:
            st.error("API_KEY not set in environment. Cannot reset system.")
    
    # Refresh button
    if st.button("Manual Refresh"):
        st.rerun()

# Auto-refresh toggle
st.markdown("### Live Threat Feed")
auto_refresh = st.checkbox("Enable Auto-Refresh", value=True, key="auto_refresh_main")
if auto_refresh:
    refresh_interval = st.slider("Refresh Interval (seconds)", min_value=1, max_value=30, value=5, key="refresh_slider")
    st_autorefresh(interval=refresh_interval * 1000, key="live_feed_refresh")

# Interactive explanation section
st.markdown("### 🧠 How ImmuniSOC-Nexus Works")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Deception Technology:**
    - Strategic placement of fake endpoints (honeytokens)
    - Attracts attackers away from real assets
    - Immediately identifies unauthorized access attempts
    """)

with col2:
    st.markdown("""
    **Real-Time Response:**
    - Instant IP quarantine upon detection
    - No manual intervention required
    - Prevents further attacks from same source
    """)

# Live threat feed
st.markdown("### 🚨 Live Threat Feed")
if st.session_state.threat_history:
    # Create a DataFrame-like structure
    threat_data = {
        "Time": [event["timestamp"] for event in st.session_state.threat_history],
        "IP Address": [event["ip"] for event in st.session_state.threat_history],
        "Threat Type": [event["trigger"] for event in st.session_state.threat_history],
        "Description": [event["description"] for event in st.session_state.threat_history],
        "Severity": [event["severity"] for event in st.session_state.threat_history]
    }
    
    # Display the dataframe
    st.dataframe(threat_data, use_container_width=True, height=300)
else:
    st.info("No threats detected yet. Use the buttons in the sidebar to simulate cyber attacks!")

# Threat analysis section
st.markdown("### 📊 Threat Analysis")

if st.session_state.current_threat_level == "SAFE":
    st.success("✅ No threats detected. System is secure and monitoring.")
    st.write("The system is actively watching for unauthorized access attempts.")
elif st.session_state.current_threat_level == "LOW":
    st.warning("🟡 Low-level threats detected. System defenses are handling automatically.")
    st.write("Monitoring for any escalation in attack patterns.")
elif st.session_state.current_threat_level == "MEDIUM":
    st.warning("⚠️ Medium threats detected. Enhanced monitoring active.")
    st.write("Multiple access attempts from various sources. Some require investigation.")
else:  # CRITICAL
    st.error("🚨 CRITICAL THREAT LEVEL: Coordinated attacks detected!")
    st.write("Defense systems are engaged. Recommend immediate review of security protocols.")

# Footer
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: #666; padding: 10px;'>ImmuniSOC-Nexus • Interactive Cybersecurity Demo • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>", unsafe_allow_html=True)

# Instructions for users
with st.expander("📋 Instructions", expanded=False):
    st.markdown("""
    **How to Use This Dashboard:**
    
    1. **Click attack simulation buttons** in the sidebar to trigger different cyber threats
    2. **Watch the metrics** update in real-time as attacks are detected
    3. **Observe the threat feed** showing detailed attack information
    4. **See the threat level** change based on attack severity
    5. **Use the reset button** to clear all data and start fresh
    
    **What You're Seeing:**
    - ImmuniSOC-Nexus uses deception technology to detect unauthorized access
    - When someone tries to access fake endpoints (honeytokens), they're immediately identified as attackers
    - The system automatically quarantines malicious IPs to prevent further attacks
    - All events are logged for security analysis and compliance
    """)