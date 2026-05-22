import os
import requests
import streamlit as st
from datetime import datetime
import time
from collections import Counter
import json

# Import st_autorefresh - this needs to be installed separately
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st.error("Please install streamlit-autorefresh: pip install streamlit-autorefresh")
    st.stop()

API_URL = os.getenv("API_URL", "http://localhost:8000")
TIMEOUT_SECONDS = 5  # Increased timeout for better reliability

# Initialize session state for storing threat history
if 'threat_history' not in st.session_state:
    st.session_state.threat_history = []

st.set_page_config(
    page_title="Neutrophil SOC Dashboard",
    page_icon="shield",
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

# Fetch current data
status_data, status_error = fetch_json("/status")
report_data, report_error = fetch_json("/report")

if status_error:
    st.error("Unable to reach the Brain API. Confirm the API is running on port 8000.")
    st.code(status_error)
    st.stop()

if report_data:
    threat_level = report_data.get("threat_level", "UNKNOWN")
else:
    threat_level = "UNKNOWN"

# Tier 1: Global Health (The Header) - Large status indicator
st.markdown("<h1 style='text-align: center;'>NEUTROPHIL SECURITY OPERATIONS CENTER</h1>", unsafe_allow_html=True)

# System status indicator with color coding
if threat_level == "CRITICAL":
    status_text = "BREACH DETECTED"
    status_color = "red"
    status_style = f"<div style='background-color: {status_color}; padding: 20px; border-radius: 10px; text-align: center; font-size: 36px; font-weight: bold; color: white; animation: pulse 1s infinite;'>{status_text}</div>"
elif threat_level == "MEDIUM":
    status_text = "THREAT DETECTED"
    status_color = "orange"
    status_style = f"<div style='background-color: {status_color}; padding: 20px; border-radius: 10px; text-align: center; font-size: 36px; font-weight: bold; color: white;'>{status_text}</div>"
elif threat_level == "SAFE":
    status_text = "SYSTEM SECURE"
    status_color = "green"
    status_style = f"<div style='background-color: {status_color}; padding: 20px; border-radius: 10px; text-align: center; font-size: 36px; font-weight: bold; color: white;'>{status_text}</div>"
else:
    status_text = "MONITORING"
    status_color = "gray"
    status_style = f"<div style='background-color: {status_color}; padding: 20px; border-radius: 10px; text-align: center; font-size: 36px; font-weight: bold; color: white;'>{status_text}</div>"

st.markdown(status_style, unsafe_allow_html=True)

# Add CSS for pulse animation
st.markdown("""
<style>
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}
</style>
""", unsafe_allow_html=True)

# Tier 2: Key Performance Indicators (The Top Row)
st.markdown("### Key Security Metrics")
alerts = status_data.get("alerts", []) if status_data else []
total_alerts = status_data.get("total_alerts", 0) if status_data else 0
unique_ips = len({alert.get("ip") for alert in alerts}) if alerts else 0

# Calculate uptime (assuming system started at the time of first alert or at a fixed time)
uptime_hours = "N/A"
if alerts:
    try:
        first_alert_time = datetime.fromisoformat(alerts[-1]["timestamp"].replace("Z", "+00:00"))
        uptime_delta = datetime.now(first_alert_time.tzinfo) - first_alert_time
        uptime_hours = f"{uptime_delta.days * 24 + uptime_delta.seconds // 3600} hours"
    except:
        uptime_hours = "Calculating..."

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="Total Attacks Blocked", 
        value=total_alerts,
        delta_color="inverse"
    )
with col2:
    st.metric(
        label="System Uptime", 
        value=uptime_hours
    )
with col3:
    st.metric(
        label="Active Quarantined IPs", 
        value=unique_ips
    )

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

# Tier 3: Event Details (The Body) - Live Threat Feed
st.markdown("### Live Threat Feed")

# Auto-refresh using st_autorefresh instead of time.sleep
auto_refresh = st.checkbox("Enable Auto-Refresh", value=True, key="auto_refresh_main")
if auto_refresh:
    refresh_interval = st.slider("Refresh Interval (seconds)", min_value=1, max_value=30, value=5, key="refresh_slider")
    st_autorefresh(interval=refresh_interval * 1000, key="live_feed_refresh")

# Create a dataframe for the threat feed
if alerts:
    # Sort by timestamp descending
    sorted_alerts = sorted(alerts, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Add to threat history
    for alert in sorted_alerts:
        if alert not in st.session_state.threat_history:
            st.session_state.threat_history.insert(0, alert)
    
    # Create a DataFrame-like structure
    threat_data = {
        "Timestamp": [alert.get("timestamp", "") for alert in st.session_state.threat_history],
        "IP Address": [alert.get("ip", "") for alert in st.session_state.threat_history],
        "Trigger": [alert.get("trigger", "") for alert in st.session_state.threat_history]
    }
    
    # Display the dataframe
    st.dataframe(threat_data, use_container_width=True, height=400)
else:
    st.info("No threats detected yet. Monitoring for suspicious activity...")

# Additional info section
st.markdown("---")
st.markdown("### System Information")
col1, col2 = st.columns(2)

with col1:
    st.write(f"**API Endpoint:** {API_URL}")
    st.write(f"**Last Refresh:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if report_data:
        st.write(f"**Current Threat Level:** {threat_level}")

with col2:
    st.write("**Service Status:**")
    # Check if services are responding
    try:
        api_check = requests.get(f"{API_URL}/status", timeout=2)
        api_status = "Running" if api_check.status_code == 200 else "Down"
    except:
        api_status = "Down"
    
    st.write(f"- Brain API: {api_status}")
    
    # Check proxy status
    try:
        proxy_check = requests.get("http://localhost:8080/status", timeout=2)
        proxy_status = "Running" if proxy_check.status_code == 200 else "Down"
    except:
        proxy_status = "Down"
    
    st.write(f"- Neutrophil Proxy: {proxy_status}")

st.markdown("---")
st.caption("Pro Tip: Enable auto-refresh in the main panel to continuously monitor threats. Use the Emergency Crisis Copilot in the sidebar for instant response guidance.")