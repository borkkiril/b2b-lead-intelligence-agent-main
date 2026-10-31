import os
import json
from typing import Dict, Any, List

CACHE_FILE = "data/app_cache.json"
KB_FILE = "data/memory/knowledge_base.json"

def ensure_dirs():
    os.makedirs("data/memory", exist_ok=True)

def load_cache():
    ensure_dirs()
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading cache: {e}")
        return {}

def save_cache(data):
    ensure_dirs()
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving cache: {e}")

def load_knowledge_base():
    ensure_dirs()
    # Import SQLite functions to ensure sync
    from core.database import init_db, sync_from_json, get_leads, count_metrics
    init_db()
    
    if not os.path.exists(KB_FILE):
        default_kb = {
            "version": "2.1.0",
            "metrics": {
                "total_leads": 0,
                "verified_live": 0,
                "not_sent": 0,
                "sent": 0,
                "replied": 0,
                "inbox_1": 0,
                "inbox_2": 0
            },
            "blacklist": [
                "Російська Федерація (RU)",
                "Білорусь (BY)",
                "Санкційні суб'єкти OFAC/EU"
            ],
            "accounts": []
        }
        return default_kb

    try:
        with open(KB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Ensure SQLite has these leads
        sync_from_json(KB_FILE)
        
        # Pull latest leads from SQLite for 100% consistency
        sqlite_leads = get_leads()
        if sqlite_leads:
            # Map SQLite leads to account format with aliases
            accounts = []
            for l in sqlite_leads:
                acc = dict(l)
                acc["name"] = l["company"]
                acc["domain"] = l["website"]
                acc["headquarters"] = l["country"]
                acc["operational_pain_trigger"] = l["industry_problem_x"]
                acc["outreach_status"] = l["status"]
                acc["cold_email"] = l["email_step1_plain_text"]
                acc["is_verified_live"] = "Verified" in l.get("mx_status", "")
                cr = l.get("contact_role", "")
                dm_name = cr
                dm_title = "Executive"
                if "(" in cr and cr.endswith(")"):
                    parts = cr[:-1].split("(", 1)
                    dm_name = parts[0].strip()
                    dm_title = parts[1].strip()
                acc["decision_maker"] = {
                    "full_name": dm_name,
                    "title": dm_title,
                    "primary_email": l["verified_email"]
                }
                accounts.append(acc)
            data["accounts"] = accounts
            m = count_metrics()
            data["metrics"] = {
                "total_leads": m["total"],
                "verified_live": m["verified"],
                "not_sent": m["not_sent"],
                "sent": m["sent"],
                "replied": m["replied"],
                "inbox_1": m["inbox_1"],
                "inbox_2": m["inbox_2"]
            }

        return data
    except Exception as e:
        print(f"Error loading knowledge base: {e}")
        return {"accounts": [], "metrics": {}}

def save_knowledge_base(data):
    ensure_dirs()
    from core.database import update_lead_status
    try:
        with open(KB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Also sync any status updates to SQLite
        accounts = data.get("accounts", [])
        for acc in accounts:
            lead_id = acc.get("id")
            st = acc.get("outreach_status") or acc.get("status")
            if lead_id and isinstance(lead_id, int) and st:
                update_lead_status(lead_id, st)
    except Exception as e:
        print(f"Error saving knowledge base: {e}")
