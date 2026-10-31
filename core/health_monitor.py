"""
System Health Monitoring & Telemetry Module for Orion.
Provides real-time health checks, SQLite ACID integrity audits, latency telemetry,
and AI generation 5-Gate quality scoring with automated webhook alerting.

Designed for DevOps / Linux / SSH production reliability and automated health auditing.
"""

import os
import sys
import time
import json
import sqlite3
import argparse
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.database import DB_FILE, get_connection

class SystemHealthReport(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    status: str  # "HEALTHY", "DEGRADED", "CRITICAL"
    db_path: str
    db_integrity: str
    db_latency_ms: float
    total_records: int
    quality_sim_score: float  # Scale 0.0 - 10.0 across 5 Gates
    metrics: Dict[str, int] = Field(default_factory=dict)
    issues: List[str] = Field(default_factory=list)
    alert_dispatched: bool = False

def calculate_leads_quality_score(conn: sqlite3.Connection) -> float:
    """
    Evaluates AI-generated lead records against the 5 Content & Deliverability QA Gates:
    1. Gate 1: Word Count (<110 words) -> 2.0 pts
    2. Gate 2: Zero Links in Email 1 -> 2.0 pts
    3. Gate 3: Valid MX status -> 2.0 pts
    4. Gate 4: Sandbox & Risk guarantee in follow-up -> 2.0 pts
    5. Gate 5: Code blueprint present -> 2.0 pts
    Returns mean score (0.0 to 10.0).
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email_step1_plain_text, email_step1_5_followup, mx_status, notion_adaptation_blueprint
        FROM leads LIMIT 100;
    """)
    rows = cursor.fetchall()
    if not rows:
        return 10.0  # Nominal score when database is fresh

    total_scores = []
    for r in rows:
        email1 = r["email_step1_plain_text"] or ""
        followup = r["email_step1_5_followup"] or ""
        mx = r["mx_status"] or ""
        blueprint = r["notion_adaptation_blueprint"] or ""

        score = 0.0
        # Gate 1: Conciseness
        words = len(email1.split())
        if 20 <= words <= 120:
            score += 2.0
        elif words > 0:
            score += 1.0

        # Gate 2: Zero links
        if "http://" not in email1 and "https://" not in email1 and words > 0:
            score += 2.0

        # Gate 3: MX live
        if "Verified" in mx or "Live" in mx:
            score += 2.0

        # Gate 4: Sandbox guarantee in follow-up
        if "Sandbox" in followup or "guarantee" in followup or "risk" in followup:
            score += 2.0
        elif followup:
            score += 1.0

        # Gate 5: Architecture blueprint
        if "```" in blueprint or "Blueprint" in blueprint:
            score += 2.0

        total_scores.append(score)

    return round(sum(total_scores) / len(total_scores), 2)

def check_system_health(
    db_path: Optional[str] = None,
    webhook_url: Optional[str] = None,
    max_latency_ms: float = 50.0,
    min_sim_score: float = 7.0
) -> Dict[str, Any]:
    """
    Runs comprehensive health and telemetry check on the Orion instance:
    - SQLite integrity check
    - Query roundtrip latency measurement (ms)
    - AI generation quality scoring
    - Alert JSON formulation
    """
    target_db = db_path or DB_FILE
    issues = []
    status = "HEALTHY"
    db_integrity = "UNKNOWN"
    latency_ms = 0.0
    total_records = 0
    sim_score = 10.0
    metrics = {}

    if not os.path.exists(target_db):
        issues.append(f"Database file does not exist at {target_db}")
        status = "CRITICAL"
        report = SystemHealthReport(
            status=status,
            db_path=target_db,
            db_integrity="FILE_NOT_FOUND",
            db_latency_ms=0.0,
            total_records=0,
            quality_sim_score=0.0,
            issues=issues
        )
        return report.model_dump()

    try:
        t0 = time.perf_counter()
        with get_connection(target_db) as conn:
            cursor = conn.cursor()
            # 1. Database latency check
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            # 2. SQLite integrity check
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()
            db_integrity = row[0] if row else "FAIL"
            if db_integrity != "ok":
                issues.append(f"SQLite PRAGMA integrity_check failed: {db_integrity}")
                status = "CRITICAL"

            # 3. Table existence & metrics
            cursor.execute("SELECT COUNT(*) FROM leads;")
            total_records = cursor.fetchone()[0]

            cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status;")
            for s_row in cursor.fetchall():
                metrics[s_row[0]] = s_row[1]

            # 4. AI Quality Score
            sim_score = calculate_leads_quality_score(conn)
    except Exception as e:
        status = "CRITICAL"
        issues.append(f"Database error during health check: {str(e)}")
        db_integrity = "EXCEPTION"

    # Evaluate latency threshold
    if latency_ms > max_latency_ms and status != "CRITICAL":
        status = "DEGRADED"
        issues.append(f"High database latency detected: {latency_ms}ms (threshold: {max_latency_ms}ms)")

    # Evaluate AI quality score threshold
    if sim_score < min_sim_score and total_records > 0 and status != "CRITICAL":
        status = "DEGRADED"
        issues.append(f"AI generation quality sim_score low: {sim_score}/10.0 (threshold: {min_sim_score}/10.0)")

    alert_dispatched = False
    if status in ["DEGRADED", "CRITICAL"] and webhook_url:
        alert_dispatched = dispatch_webhook_alert(webhook_url, status, issues, latency_ms, sim_score)

    report = SystemHealthReport(
        status=status,
        db_path=target_db,
        db_integrity=db_integrity,
        db_latency_ms=latency_ms,
        total_records=total_records,
        quality_sim_score=sim_score,
        metrics=metrics,
        issues=issues,
        alert_dispatched=alert_dispatched
    )
    return report.model_dump()

def dispatch_webhook_alert(
    webhook_url: str,
    status: str,
    issues: List[str],
    latency_ms: float,
    sim_score: float
) -> bool:
    """Dispatches JSON alert payload to external Slack / PagerDuty / monitoring webhook."""
    payload = {
        "text": f"🚨 [Orion Alert] System status changed to *{status}*",
        "status": status,
        "latency_ms": latency_ms,
        "sim_score": sim_score,
        "issues": issues,
        "timestamp": time.time()
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return resp.status in [200, 201, 204]
    except Exception as e:
        print(f"[WARN] Failed to send webhook alert: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Orion system health and telemetry.")
    parser.add_argument("--db", type=str, default=DB_FILE, help="Path to SQLite database.")
    parser.add_argument("--webhook", type=str, default=None, help="Slack / Webhook alert URL.")
    parser.add_argument("--max-latency", type=float, default=50.0, help="Max latency threshold (ms).")
    parser.add_argument("--min-score", type=float, default=7.0, help="Min quality score (0-10).")
    parser.add_argument("--json", action="store_true", help="Output pure JSON report.")
    args = parser.parse_args()

    health = check_system_health(
        db_path=args.db,
        webhook_url=args.webhook,
        max_latency_ms=args.max_latency,
        min_sim_score=args.min_score
    )

    if args.json:
        print(json.dumps(health, indent=2))
    else:
        status_color = "🟢" if health["status"] == "HEALTHY" else ("🟡" if health["status"] == "DEGRADED" else "🔴")
        print(f"{status_color} Orion System Health: {health['status']}")
        print(f"  - Database: {health['db_path']} (Integrity: {health['db_integrity']})")
        print(f"  - Latency: {health['db_latency_ms']} ms")
        print(f"  - Total Records: {health['total_records']}")
        print(f"  - 5-Gate AI Quality: {health['quality_sim_score']}/10.0")
        if health["issues"]:
            print("  - Issues Detected:")
            for issue in health["issues"]:
                print(f"    * {issue}")

    sys.exit(0 if health["status"] == "HEALTHY" else 1)
