from fastapi import FastAPI, HTTPException, Depends, HTTPException  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, IPvAnyAddress
from datetime import datetime
from typing import List
import os
import sqlite3
import json
import secrets

app = FastAPI(
    title="ImmuniSOC-Nexus Brain API",
    description="API for the ImmuniSOC-Nexus deception proxy system",
    version="1.0.0"
)

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

def verify_api_key(x_api_key: str = None):
    """Verify the API key from environment variable."""
    expected_api_key = os.getenv("API_KEY")
    if not expected_api_key:
        # Generate a random API key if not set
        import secrets
        expected_api_key = secrets.token_urlsafe(32)
        os.environ["API_KEY"] = expected_api_key
    
    if not x_api_key or x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")

# Database setup
DB_PATH = "alerts.db"

def init_db():
    """Initialize the SQLite database with alerts table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create alerts table with proper schema
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

# Helper function to validate and convert IP
def validate_ip(ip: str) -> str:
    """Validate and normalize IP address."""
    try:
        # This will raise an exception if the IP is invalid
        validated_ip = IPvAnyAddress.validate_python(ip)
        return str(validated_ip)
    except Exception:
        raise ValueError(f"Invalid IP address: {ip}")

# Context manager for database connections
@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

# Async function to generate threat report
async def generate_threat_report(report: ReportResponse = None):
    """Generate a threat report file."""
    try:
        if report is None:
            # Get current report
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT ip FROM alerts")
                unique_ips = [row[0] for row in cursor.fetchall()]
                
                cursor.execute("SELECT ip, trigger, timestamp FROM alerts ORDER BY timestamp DESC")
                all_alerts = [
                    {"ip": ip, "trigger": trigger, "timestamp": timestamp}
                    for ip, trigger, timestamp in cursor.fetchall()
                ]
            
            total_incidents = len(all_alerts)
            
            if total_incidents == 0:
                threat_level = "SAFE"
            elif total_incidents <= 3 and len(unique_ips) <= 2:
                threat_level = "LOW"
            elif total_incidents <= 10 or len(unique_ips) <= 5:
                threat_level = "MEDIUM"
            else:
                threat_level = "CRITICAL"
            
            if threat_level == "SAFE":
                summary = "No intrusion attempts detected. The deception mesh is active and healthy."
                layman_explanation = "Everything is normal. The digital security guards are patrolling the perimeter, and no alarms have been triggered."
                recommendations = [
                    "Maintain standard operations. No emergency actions required.",
                    "Verify that staff understand basic password safety and phishing awareness."
                ]
            elif threat_level == "LOW":
                summary = "Minor intrusion attempts detected. Automated defenses have contained the threats."
                layman_explanation = "A few suspicious activities were detected and automatically blocked. Think of it as a few curious visitors who wandered into restricted areas and were escorted out."
                recommendations = [
                    "Monitor the situation closely for any recurring patterns.",
                    "Review access logs for any anomalies that might have been missed."
                ]
            elif threat_level == "MEDIUM":
                summary = "Multiple intrusion attempts detected. Defense mechanisms are actively engaged."
                layman_explanation = "Several attempts to access restricted areas have been detected and blocked. This suggests a more coordinated effort to breach security measures."
                recommendations = [
                    "Increase monitoring of affected systems.",
                    "Consider temporarily restricting access to sensitive areas if pattern continues.",
                    "Brief IT security team on recent attack vectors."
                ]
            else:  # CRITICAL
                summary = "Significant security breach attempts detected. Immediate attention required."
                layman_explanation = "Multiple systematic attempts to breach security have been detected. The system has automatically blocked these attempts, but human oversight is needed."
                recommendations = [
                    "Escalate to senior security personnel immediately.",
                    "Conduct comprehensive audit of all access logs.",
                    "Prepare incident response procedures.",
                    "Consider isolating affected systems if pattern persists."
                ]
            
            report = ReportResponse(
                timestamp=datetime.utcnow().isoformat() + "Z",
                threat_level=threat_level,
                total_incidents=total_incidents,
                quarantined_ips=unique_ips,
                summary=summary,
                layman_explanation=layman_explanation,
                recommendations=recommendations,
                incidents=all_alerts
            )
        
        # Write to threat report file
        with open("threat_report.md", "w") as f:
            f.write(f"# IMMUNISOC-NEXUS THREAT REPORT\n\n")
            f.write(f"**Generated at:** {report.timestamp}\n\n")
            f.write(f"## Threat Level: {report.threat_level}\n\n")
            f.write(f"### Summary\n{report.summary}\n\n")
            f.write(f"### Layman Explanation\n{report.layman_explanation}\n\n")
            f.write(f"### Recommendations\n")
            for rec in report.recommendations:
                f.write(f"- {rec}\n")
            f.write(f"\n### Quarantined IPs\n")
            for ip in report.quarantined_ips:
                f.write(f"- {ip}\n")
            f.write(f"\n### Incidents\n")
            for incident in report.incidents[:10]:  # Limit to last 10 incidents
                f.write(f"- {incident['timestamp']}: {incident['ip']} triggered '{incident['trigger']}'\n")
            if len(report.incidents) > 10:
                f.write(f"... and {len(report.incidents) - 10} more incidents\n")
        
    except Exception as e:
        print(f"Error generating threat report: {e}")

# --- Pydantic Data Policing (Validation Schemas) ---

class AlertPayload(BaseModel):
    ip: str = Field(..., example="127.0.0.1", description="Attacker IP address")
    trigger: str = Field(..., example="honeytoken_accessed", description="Deception trap trigger type")

class Alert(BaseModel):
    ip: IPvAnyAddress  # Validates any IP address format
    trigger: str

class AlertResponse(BaseModel):
    message: str
    timestamp: str
    ip: str

class StatusResponse(BaseModel):
    total_alerts: int
    alerts: List[Dict]

class ReportResponse(BaseModel):
    timestamp: str
    threat_level: str
    total_incidents: int
    quarantined_ips: List[str]
    summary: str
    layman_explanation: str
    recommendations: List[str]
    incidents: List[Dict]

# --- Endpoints ---

@app.post("/alert", response_model=AlertResponse)
async def create_alert(alert: Alert, api_key: str = Depends(verify_api_key)):
    """
    Create a new alert from the deception proxy.
    The proxy calls this when it detects suspicious activity.
    """
    try:
        # Validate and normalize the IP
        validated_ip = validate_ip(str(alert.ip))
        
        # Store alert in database
        timestamp = datetime.utcnow().isoformat() + "Z"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO alerts (ip, trigger, timestamp) VALUES (?, ?, ?)",
                (validated_ip, alert.trigger, timestamp)
            )
            conn.commit()
        
        # Write to JSON file for backup/diagnostic purposes
        alert_entry = {
            "ip": validated_ip,
            "trigger": alert.trigger,
            "timestamp": timestamp
        }
        
        # Read existing alerts from JSON file
        alerts_file = "alerts.json"
        existing_alerts = []
        if os.path.exists(alerts_file):
            try:
                with open(alerts_file, "r") as f:
                    existing_alerts = json.load(f)
            except json.JSONDecodeError:
                existing_alerts = []
        
        # Append new alert
        existing_alerts.append(alert_entry)
        
        # Write back to JSON file
        with open(alerts_file, "w") as f:
            json.dump(existing_alerts, f, indent=2)
        
        # Write to threat report file
        await generate_threat_report()
        
        return AlertResponse(
            message="Alert received and processed",
            timestamp=timestamp,
            ip=validated_ip
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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

    # Write to threat report file
    await generate_threat_report(report_data)
    
    return report_data
    except Exception as e:
        print(f"Error writing audit report file: {e}")

    return report_data

# Reset endpoint for clean demo resets
@app.post("/reset")
async def reset_system(api_key: str = Depends(verify_api_key)):
    """Reset all alerts from the system."""
    try:
        # Clear database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alerts")
            conn.commit()
        
        # Clear JSON file
        if os.path.exists("alerts.json"):
            with open("alerts.json", "w") as f:
                json.dump([], f)
        
        # Clear threat report
        if os.path.exists("threat_report.md"):
            os.remove("threat_report.md")
        
        return {"message": "System reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)