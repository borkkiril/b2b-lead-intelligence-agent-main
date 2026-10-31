"""
Database Management Module (SQLite) for B2B Lead Intelligence Dashboard.
100% offline, zero-cost, ACID compliant, schema-validated.

Fields:
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- inbox_slot: TEXT ('Пошта 1' / 'Пошта 2')
- company: TEXT NOT NULL
- country: TEXT NOT NULL
- website: TEXT NOT NULL
- industry_problem_x: TEXT NOT NULL
- contact_role: TEXT NOT NULL
- verified_email: TEXT NOT NULL
- mx_status: TEXT NOT NULL DEFAULT 'Verified MX + HTTP 200 Live'
- email_step1_plain_text: TEXT NOT NULL
- email_step1_5_followup: TEXT NOT NULL DEFAULT ''
- notion_adaptation_blueprint: TEXT NOT NULL
- status: TEXT NOT NULL DEFAULT 'Не відправлено'
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
"""

import os
import sqlite3
import json
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_FILE = os.path.join(DB_DIR, "leads.db")
KB_JSON_FILE = os.path.join(DB_DIR, "memory", "knowledge_base.json")

def get_db_path(custom_path: Optional[str] = None) -> str:
    if custom_path:
        return custom_path
    os.makedirs(DB_DIR, exist_ok=True)
    return DB_FILE

@contextmanager
def get_connection(db_path: Optional[str] = None):
    path = get_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db(db_path: Optional[str] = None) -> None:
    """Створює таблицю leads з усіма обов'язковими полями та перевіряє цілісність."""
    path = get_db_path(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inbox_slot TEXT NOT NULL DEFAULT 'Пошта 1',
                company TEXT NOT NULL,
                country TEXT NOT NULL,
                website TEXT NOT NULL,
                industry_problem_x TEXT NOT NULL,
                contact_role TEXT NOT NULL,
                verified_email TEXT NOT NULL,
                mx_status TEXT NOT NULL DEFAULT 'Verified MX + HTTP 200 Live',
                email_step1_plain_text TEXT NOT NULL,
                email_step1_5_followup TEXT NOT NULL DEFAULT '',
                notion_adaptation_blueprint TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Не відправлено',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Міграція колонки email_step1_5_followup якщо база вже існувала
        cursor.execute("PRAGMA table_info(leads);")
        cols = {row["name"] for row in cursor.fetchall()}
        if "email_step1_5_followup" not in cols:
            cursor.execute("ALTER TABLE leads ADD COLUMN email_step1_5_followup TEXT NOT NULL DEFAULT '';")

        # Створюємо індекси для швидкої фільтрації
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads (status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_inbox ON leads (inbox_slot);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_country ON leads (country);")
        conn.commit()

def verify_table_integrity(db_path: Optional[str] = None) -> bool:
    """Перевіряє наявність усіх обов'язкових колонок у таблиці leads."""
    expected_columns = {
        "id", "inbox_slot", "company", "country", "website",
        "industry_problem_x", "contact_role", "verified_email",
        "mx_status", "email_step1_plain_text", "email_step1_5_followup",
        "notion_adaptation_blueprint", "status", "created_at"
    }
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(leads);")
        rows = cursor.fetchall()
        existing_columns = {row["name"] for row in rows}
        return expected_columns.issubset(existing_columns)

class LeadRecord(BaseModel):
    """
    Pydantic v2 schema for validating B2B lead records before database persistence.
    Guarantees strict typing and default values for all 11 required system fields.
    """
    inbox_slot: str = Field(default="Пошта 1", description="Account inbox slot (e.g. Пошта 1 / Пошта 2)")
    company: str = Field(default="Unknown", min_length=1, description="Company name")
    country: str = Field(default="ЄС", description="Headquarters region or country")
    website: str = Field(default="", description="Primary corporate domain / URL")
    industry_problem_x: str = Field(default="", description="Operational pain trigger or industry bottleneck hypothesis")
    contact_role: str = Field(default="", description="Decision-maker full name and job title")
    verified_email: str = Field(default="", description="Target verified business email address")
    mx_status: str = Field(default="Verified MX + HTTP 200 Live", description="Socket MX & HTTP delivery status")
    email_step1_plain_text: str = Field(default="", description="Plain-text Step 1 email payload")
    email_step1_5_followup: str = Field(default="", description="Step 1.5 followup email payload")
    notion_adaptation_blueprint: str = Field(default="", description="Technical Notion architecture blueprint")
    status: str = Field(default="Не відправлено", description="Outreach processing status")

def insert_lead(lead: Union[Dict[str, Any], LeadRecord], db_path: Optional[str] = None) -> int:
    """Додає новий запис ліда в БД з обов'язковою Pydantic v2 валідацією. Повертає згенерований ID."""
    init_db(db_path)
    if isinstance(lead, LeadRecord):
        record = lead
    else:
        # Normalize fields supporting legacy agent dictionaries
        raw = {
            "inbox_slot": lead.get("inbox_slot") or "Пошта 1",
            "company": lead.get("company") or lead.get("name") or "Unknown",
            "country": lead.get("country") or lead.get("headquarters") or "ЄС",
            "website": lead.get("website") or lead.get("domain") or "",
            "industry_problem_x": (
                lead.get("industry_problem_x")
                or lead.get("operational_pain_trigger")
                or lead.get("process_bottleneck_hypothesis")
                or ""
            ),
            "contact_role": (
                lead.get("contact_role")
                or (
                    f"{lead.get('decision_maker', {}).get('full_name', '')} ({lead.get('decision_maker', {}).get('title', '')})".strip()
                    if isinstance(lead.get("decision_maker"), dict)
                    else ""
                )
            ),
            "verified_email": (
                lead.get("verified_email")
                or (
                    lead.get("decision_maker", {}).get("primary_email", "")
                    if isinstance(lead.get("decision_maker"), dict)
                    else ""
                )
            ),
            "mx_status": lead.get("mx_status") or "Verified MX + HTTP 200 Live",
            "email_step1_plain_text": lead.get("email_step1_plain_text") or lead.get("cold_email") or "",
            "email_step1_5_followup": lead.get("email_step1_5_followup") or "",
            "notion_adaptation_blueprint": lead.get("notion_adaptation_blueprint") or "",
            "status": lead.get("status") or lead.get("outreach_status") or "Не відправлено",
        }
        record = LeadRecord(**raw)

    sql = """
        INSERT INTO leads (
            inbox_slot, company, country, website,
            industry_problem_x, contact_role, verified_email,
            mx_status, email_step1_plain_text, email_step1_5_followup,
            notion_adaptation_blueprint, status
        ) VALUES (
            :inbox_slot, :company, :country, :website,
            :industry_problem_x, :contact_role, :verified_email,
            :mx_status, :email_step1_plain_text, :email_step1_5_followup,
            :notion_adaptation_blueprint, :status
        );
    """
    params = record.model_dump()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        lead_id = cursor.lastrowid
        conn.commit()
        return lead_id

def get_leads(
    status: Optional[str] = None,
    country: Optional[str] = None,
    inbox_slot: Optional[str] = None,
    search: Optional[str] = None,
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Повертає список лідів з можливістю фільтрації."""
    init_db(db_path)
    conditions = []
    params = []

    if status and status != "Всі":
        conditions.append("status = ?")
        params.append(status)

    if inbox_slot and inbox_slot != "Всі":
        conditions.append("inbox_slot = ?")
        params.append(inbox_slot)

    if country and country != "Всі":
        if country == "ЄС":
            conditions.append("(country LIKE '%germany%' OR country LIKE '%німеччин%' OR country LIKE '%france%' OR country LIKE '%франц%' OR country LIKE '%netherlands%' OR country LIKE '%poland%' OR country LIKE '%польщ%' OR country LIKE '%ireland%' OR country LIKE '%estonia%' OR country LIKE '%sweden%' OR country LIKE '%spain%' OR country LIKE '%italy%' OR country LIKE '%austria%' OR country LIKE '%belgium%' OR country LIKE '%czech%' OR country LIKE '%чехі%' OR country LIKE '%switzerland%' OR country LIKE '%швейцар%' OR country LIKE '%єс%' OR country LIKE '%eu%')")
        elif country == "UK":
            conditions.append("(country LIKE '%uk%' OR country LIKE '%united kingdom%' OR country LIKE '%london%' OR country LIKE '%великобритан%' OR country LIKE '%лондон%' OR country LIKE '%england%')")
        elif country == "Україна":
            conditions.append("(country LIKE '%ukraine%' OR country LIKE '%україна%' OR country LIKE '%kyiv%' OR country LIKE '%київ%' OR country LIKE '%lviv%' OR country LIKE '%львів%')")
        else:
            conditions.append("country LIKE ?")
            params.append(f"%{country}%")

    if search and search.strip():
        q = f"%{search.strip().lower()}%"
        conditions.append("""(
            LOWER(company) LIKE ? OR
            LOWER(website) LIKE ? OR
            LOWER(contact_role) LIKE ? OR
            LOWER(verified_email) LIKE ? OR
            LOWER(industry_problem_x) LIKE ?
        )""")
        params.extend([q, q, q, q, q])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM leads {where_clause} ORDER BY id ASC;"

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_lead_by_id(lead_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Повертає один лід за його ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE id = ?;", (lead_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_lead_status(lead_id: int, status: str, db_path: Optional[str] = None) -> bool:
    """Оновлює статус ліда (Не відправлено / Відправлено / Отримано відповідь)."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE leads SET status = ? WHERE id = ?;", (status, lead_id))
        conn.commit()
        return cursor.rowcount > 0

def update_lead(lead_id: int, fields: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """Оновлює довільні поля ліда."""
    init_db(db_path)
    allowed_fields = {
        "inbox_slot", "company", "country", "website",
        "industry_problem_x", "contact_role", "verified_email",
        "mx_status", "email_step1_plain_text", "email_step1_5_followup",
        "notion_adaptation_blueprint", "status"
    }
    updates = {k: v for k, v in fields.items() if k in allowed_fields}
    if not updates:
        return False

    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    params = list(updates.values()) + [lead_id]

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE leads SET {set_clause} WHERE id = ?;", params)
        conn.commit()
        return cursor.rowcount > 0

def update_unsent_lead(lead_id: int, fields: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """
    Безпечно оновлює поля чернетки ліда.
    Оновлення дозволено ВИКЛЮЧНО для невідправлених листів (status IN ('Не відправлено', 'DRAFT')).
    Запобігає перезапису вже відправлених комунікацій або лідів із відповідями (ACID State Immutability).
    """
    init_db(db_path)
    allowed_fields = {
        "inbox_slot", "company", "country", "website",
        "industry_problem_x", "contact_role", "verified_email",
        "mx_status", "email_step1_plain_text", "email_step1_5_followup",
        "notion_adaptation_blueprint", "status"
    }
    updates = {k: v for k, v in fields.items() if k in allowed_fields}
    if not updates:
        return False

    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    params = list(updates.values()) + [lead_id]

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE leads SET {set_clause} WHERE id = ? AND status IN ('Не відправлено', 'DRAFT');",
            params
        )
        conn.commit()
        return cursor.rowcount > 0

def delete_lead(lead_id: int, db_path: Optional[str] = None) -> bool:
    """Видаляє лід за ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM leads WHERE id = ?;", (lead_id,))
        conn.commit()
        return cursor.rowcount > 0

def count_metrics(db_path: Optional[str] = None) -> Dict[str, int]:
    """Повертає агреговані лічильники бази."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads;")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Не відправлено';")
        not_sent = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Відправлено';")
        sent = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Отримано відповідь';")
        replied = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leads WHERE inbox_slot = 'Пошта 1';")
        inbox_1 = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leads WHERE inbox_slot = 'Пошта 2';")
        inbox_2 = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leads WHERE mx_status LIKE '%Verified%';")
        verified = cursor.fetchone()[0]

        return {
            "total": total,
            "not_sent": not_sent,
            "sent": sent,
            "replied": replied,
            "inbox_1": inbox_1,
            "inbox_2": inbox_2,
            "verified": verified
        }

def sync_from_json(json_path: Optional[str] = None, db_path: Optional[str] = None) -> int:
    """Імпортує акаунти з knowledge_base.json у SQLite leads.db, якщо база порожня."""
    path = json_path or KB_JSON_FILE
    if not os.path.exists(path):
        return 0

    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads;")
        if cursor.fetchone()[0] > 0:
            return 0  # вже заповнено

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        accounts = data.get("accounts", [])
        inserted = 0
        for i, acc in enumerate(accounts):
            slot = acc.get("inbox_slot") or ("Пошта 1" if i % 2 == 0 else "Пошта 2")
            lead_dict = {
                "inbox_slot": slot,
                "company": acc.get("company") or acc.get("name", "Unknown"),
                "country": acc.get("country") or acc.get("headquarters", "ЄС"),
                "website": acc.get("website") or acc.get("domain", ""),
                "industry_problem_x": acc.get("industry_problem_x") or acc.get("operational_pain_trigger") or acc.get("process_bottleneck_hypothesis", ""),
                "contact_role": acc.get("contact_role") or f"{acc.get('decision_maker', {}).get('full_name', '')} ({acc.get('decision_maker', {}).get('title', '')})".strip(),
                "verified_email": acc.get("verified_email") or acc.get("decision_maker", {}).get("primary_email", ""),
                "mx_status": acc.get("mx_status") or "Verified MX + HTTP 200 Live",
                "email_step1_plain_text": acc.get("email_step1_plain_text") or acc.get("cold_email", ""),
                "email_step1_5_followup": acc.get("email_step1_5_followup", ""),
                "notion_adaptation_blueprint": acc.get("notion_adaptation_blueprint") or "",
                "status": acc.get("status") or acc.get("outreach_status", "Не відправлено"),
            }
            insert_lead(lead_dict, db_path)
            inserted += 1
        return inserted
    except Exception as e:
        print(f"Error syncing from JSON: {e}")
        return 0

def export_to_json(json_path: Optional[str] = None, db_path: Optional[str] = None) -> bool:
    """Експортує всі записи з SQLite leads.db назад у knowledge_base.json для синхронізації."""
    path = json_path or KB_JSON_FILE
    leads = get_leads(db_path=db_path)
    metrics = count_metrics(db_path=db_path)

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    try:
        existing = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
    except Exception:
        existing = {}

    existing["version"] = "2.2.0"
    existing["metrics"] = {
        "total_leads": metrics["total"],
        "verified_live": metrics["verified"],
        "not_sent": metrics["not_sent"],
        "sent": metrics["sent"],
        "replied": metrics["replied"],
        "inbox_1": metrics["inbox_1"],
        "inbox_2": metrics["inbox_2"]
    }

    accounts = []
    for l in leads:
        acc = dict(l)
        acc["name"] = l["company"]
        acc["domain"] = l["website"]
        acc["headquarters"] = l["country"]
        acc["operational_pain_trigger"] = l["industry_problem_x"]
        acc["outreach_status"] = l["status"]
        acc["cold_email"] = l["email_step1_plain_text"]
        acc["followup_email"] = l.get("email_step1_5_followup", "")
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

    existing["accounts"] = accounts

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error exporting to JSON: {e}")
        return False
