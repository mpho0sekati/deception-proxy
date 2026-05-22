from fastapi import FastAPI, HTTPException, Depends  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
import os
import sqlite3
import json
import secrets

app = FastAPI(title="Neutrophil Deception Brain API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key configuration
API_KEY = os.getenv("API_KEY", secrets.token_urlsafe(32))  # Generate a random API key if not set
API_KEY_NAME = "X-API-Key"

def get_api_key(api_key_header: str = Depends(lambda: os.getenv("API_KEY"))):
    """Dependency to check for valid API key on write endpoints."""
    def api_key_dependency(header: str = None):
        if header != api_key_header:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        return header
    return api_key_dependency

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            trigger TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database on startup
init_db()

# Function to persist alerts to JSON file as well
def persist_to_json():
    """Persist alerts from SQLite to JSON file."""
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute("SELECT ip, trigger, timestamp FROM alerts ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    
    alerts_list = [{"ip": row[0], "trigger": row[1], "timestamp": row[2]} for row in rows]
    
    # Write to JSON file
    with open('alerts.json', 'w') as f:
        json.dump(alerts_list, f, indent=2)

# --- Pydantic Data Policing (Validation Schemas) ---

class AlertPayload(BaseModel):
    ip: str = Field(..., example="127.0.0.1", description="Attacker IP address")
    trigger: str = Field(..., example="honeytoken_accessed", description="Deception trap trigger type")

class SecurityReport(BaseModel):
    timestamp: str
    threat_level: str
    total_incidents: int
    quarantined_ips: List[str]
    summary: str
    layman_explanation: str
    recommendations: List[str]
    incidents: List[AlertPayload]

# --- Endpoints ---

@app.post("/alert")
def create_alert(payload: AlertPayload, api_key: str = Depends(get_api_key(API_KEY))):
    # Validate IP format (basic validation)
    import ipaddress
    try:
        ipaddress.ip_address(payload.ip)
    except ValueError:
        return {"status": "error", "message": "Invalid IP address format"}
    
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    alert = {
        "ip": payload.ip,
        "trigger": payload.trigger,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    cursor.execute(
        "INSERT INTO alerts (ip, trigger, timestamp) VALUES (?, ?, ?)",
        (payload.ip, payload.trigger, alert["timestamp"])
    )
    conn.commit()
    conn.close()
    
    # Persist to JSON as well
    persist_to_json()
    
    return {"status": "received", "alert": alert}

@app.get("/status")
def get_status():
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute("SELECT ip, trigger, timestamp FROM alerts ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    
    alerts = [{"ip": row[0], "trigger": row[1], "timestamp": row[2]} for row in rows]
    
    return {
        "total_alerts": len(alerts),
        "alerts": alerts
    }

@app.get("/report", response_model=SecurityReport)
def generate_report():
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute("SELECT ip, trigger, timestamp FROM alerts ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    
    alerts_db = [{"ip": row[0], "trigger": row[1], "timestamp": row[2]} for row in rows]
    
    unique_ips = list(set([alert["ip"] for alert in alerts_db]))
    count = len(alerts_db)
    
    if count == 0:
        threat_level = "SAFE"
        summary = "No intrusion attempts detected. The deception mesh is active and healthy."
        layman_explanation = "Everything is normal. The digital security guards are patrolling the perimeter, and no alarms have been triggered."
        recommendations = [
            "Maintain standard operations. No emergency actions required.",
            "Verify that staff understand basic password safety and phishing awareness."
        ]
    elif count == 1:
        threat_level = "MEDIUM"
        summary = f"A single honeytoken access attempt was detected and quarantined from IP: {unique_ips[0]}."
        layman_explanation = (
            f"An unauthorized device (IP: {unique_ips[0]}) tried to access a hidden trapdoor "
            f"designed to look like sensitive financial archives. Our system immediately detected "
            f"this, locked the door, and quarantined that device. They can no longer access any part of our network."
        )
        recommendations = [
            "Notify your local IT administrator or external support provider that an unauthorized device has been locked out.",
            "Check if any internal staff members were trying to access files they shouldn't be looking at (insider threat review).",
            "Keep the system running to maintain the lock on the unauthorized device."
        ]
    else:
        threat_level = "CRITICAL"
        summary = f"Multiple lateral movement attempts detected across {len(unique_ips)} source IPs. Active threat quarantine is engaged."
        layman_explanation = (
            f"A coordinated network intrusion is underway. Multiple devices/computers on your network "
            f"are trying to scan and steal sensitive organization records. Our active deception mesh has "
            f"quarantined {len(unique_ips)} different machines, shutting down their access to protect your files."
        )
        recommendations = [
            "Immediately notify executive leadership and your external security response partner.",
            "Unplug affected network cables if physical systems are suspected of being compromised, but do not turn off the main server.",
            "Contact the South African National CSIRT (Cyber Security Incident Response Team) or cyber crime unit for containment guidance."
        ]

    # Structure and validate report data using Pydantic
    report_data = SecurityReport(
        timestamp=datetime.utcnow().isoformat() + "Z",
        threat_level=threat_level,
        total_incidents=count,
        quarantined_ips=unique_ips,
        summary=summary,
        layman_explanation=layman_explanation,
        recommendations=recommendations,
        incidents=[AlertPayload(ip=a["ip"], trigger=a["trigger"]) for a in alerts_db]
    )

    # Write report file to disk for audit compliance
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "threat_report.md")
    try:
        with open(report_path, "w") as f:
            f.write(f"# SECURITY INCIDENT AUDIT & RESPONSE BRIEF\n")
            f.write(f"Generated at: {report_data.timestamp}\n\n")
            f.write(f"## Threat Level: **{report_data.threat_level}**\n\n")
            f.write(f"### Plain-English Event Explanation\n{report_data.layman_explanation}\n\n")
            f.write(f"### Technical Summary\n{report_data.summary}\n\n")
            f.write(f"### Quarantined Devices (IPs)\n")
            for ip in report_data.quarantined_ips:
                f.write(f"- {ip}\n")
            f.write(f"\n### Action Checklist for Staff\n")
            for rec in report_data.recommendations:
                f.write(f"- [ ] {rec}\n")
            f.write(f"\n### Incident Logs\n")
            for idx, incident in enumerate(report_data.incidents):
                f.write(f"{idx+1}. **Device IP**: `{incident.ip}` | **Trap Trigger**: `{incident.trigger}`\n")
    except Exception as e:
        print(f"Error writing audit report file: {e}")

    return report_data

# Reset endpoint for clean demo resets
@app.post("/reset")
def reset_system(api_key: str = Depends(get_api_key(API_KEY))):
    """Reset the system by clearing all alerts from the database."""
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alerts")
    conn.commit()
    conn.close()
    
    # Also clear the JSON file
    if os.path.exists('alerts.json'):
        os.remove('alerts.json')
    
    # Clear the threat report
    if os.path.exists('threat_report.md'):
        os.remove('threat_report.md')
    
    return {"status": "reset", "message": "System reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)