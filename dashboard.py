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
    page_title="ImmuniSOC-Nexus Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
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
st.markdown("<h1 style='text-align: center;'>ImmuniSOC-Nexus DASHBOARD</h1>", unsafe_allow_html=True)

# System status indicator with color coding
if threat_level == "CRITICAL":
    status_text = "CRITICAL THREAT DETECTED"
    status_color = "#D32F2F"  # Dark red
    status_style = f"<div style='background-color: {status_color}; padding: 25px; border-radius: 10px; text-align: center; font-size: 32px; font-weight: bold; color: white; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>🔴 {status_text}</div>"
elif threat_level == "MEDIUM":
    status_text = "MEDIUM THREAT DETECTED"
    status_color = "#FF8F00"  # Amber
    status_style = f"<div style='background-color: {status_color}; padding: 25px; border-radius: 10px; text-align: center; font-size: 32px; font-weight: bold; color: white; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>🟡 {status_text}</div>"
elif threat_level == "LOW":
    status_text = "MINOR THREAT DETECTED"
    status_color = "#FFB300"  # Light amber
    status_style = f"<div style='background-color: {status_color}; padding: 25px; border-radius: 10px; text-align: center; font-size: 32px; font-weight: bold; color: white; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>🟡 {status_text}</div>"
elif threat_level == "SAFE":
    status_text = "SYSTEM SECURE"
    status_color = "#388E3C"  # Dark green
    status_style = f"<div style='background-color: {status_color}; padding: 25px; border-radius: 10px; text-align: center; font-size: 32px; font-weight: bold; color: white; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>🟢 {status_text}</div>"
else:
    status_text = "MONITORING"
    status_color = "#757575"  # Gray
    status_style = f"<div style='background-color: {status_color}; padding: 25px; border-radius: 10px; text-align: center; font-size: 32px; font-weight: bold; color: white; margin-bottom: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>🔵 {status_text}</div>"

st.markdown(status_style, unsafe_allow_html=True)

# Key metrics in cards
alerts = status_data.get("alerts", []) if status_data else []
total_alerts = status_data.get("total_alerts", 0) if status_data else 0
unique_ips = len({alert.get("ip") for alert in alerts}) if alerts else 0

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3 style="color: #1E88E5; margin-bottom: 10px;">🛡️ Attacks Blocked</h3>
        <h2 style="color: #0D47A1; font-size: 36px; margin: 0;">{total_alerts}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3 style="color: #1E88E5; margin-bottom: 10px;">🔒 IPs Quarantined</h3>
        <h2 style="color: #0D47A1; font-size: 36px; margin: 0;">{unique_ips}</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3 style="color: #1E88E5; margin-bottom: 10px;">📊 Threat Level</h3>
        <h2 style="color: #0D47A1; font-size: 36px; margin: 0;">{threat_level}</h2>
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
    st.dataframe(threat_data, use_container_width=True, height=300)
else:
    st.info("No threats detected yet. Monitoring for suspicious activity...")

# Threat summary section
if report_data:
    st.markdown("### Threat Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Summary:** {report_data.get('summary', 'No summary available.')}")
        st.markdown(f"**Explanation:** {report_data.get('layman_explanation', 'No explanation available.')}")
    
    with col2:
        st.markdown("**Recommendations:**")
        for rec in report_data.get('recommendations', []):
            st.markdown(f"- {rec}")

# Footer
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: #666; padding: 10px;'>ImmuniSOC-Nexus • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • API: {API_URL}</div>", unsafe_allow_html=True)