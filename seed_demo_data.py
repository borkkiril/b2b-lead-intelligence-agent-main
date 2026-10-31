"""
Demo Data Seeder (Safe Mock Dataset for Live Demo & Public GitHub Screenshots).
Populates SQLite leads.db with 3 fictitious B2B companies:
1. UK (London) — Apex Settlement Labs Ltd (FinTech / Open Banking)
2. Germany (Berlin) — Vanguard Cargo Logistics GmbH (Freight / Supply Chain)
3. Ukraine (Kyiv) — NovaFlow Intelligence Ltd (B2B SaaS / Workflow Engine)

100% Zero-Leak: All company names, contacts, and emails use RFC 2606 reserved domains (.example.com).
Complies with all 11 database schema columns, 0-link cold email constraint, and Staging Sandbox blueprints.
"""

import os
import sys
import argparse

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.database import init_db, insert_lead, get_leads, count_metrics, get_connection, DB_FILE

DEMO_COMPANIES = [
    {
        "inbox_slot": "Пошта 1",
        "company": "Apex Settlement Labs Ltd",
        "country": "🇬🇧 UK (London)",
        "website": "apex-settlement.example.com",
        "industry_problem_x": "Розсинхрон черги асинхронних вебхуків Open Banking та розбіжності у клірингових реєстрах BACS проти балансів мерчантів під час пікових навантажень.",
        "contact_role": "Oliver Vance (Co-Founder & CEO)",
        "verified_email": "oliver.vance@apex-settlement.example.com",
        "mx_status": "Verified MX (Google Workspace) + HTTP 200 Live",
        "email_step1_plain_text": """Subject: Apex Settlement Open Banking ledger reconciliation

Hi Oliver,

Analyzing API-first payment infrastructure at your volume, we frequently see a core operational bottleneck: manual engineering hours spent reconciling asynchronous webhook batch settlements against merchant ledgers.

We built an isolated staging pipeline with idempotent queue verification that guarantees 100% ledger consistency with zero latency impact. We adapt this completely asynchronously without meetings.

If you are open to an async audit with guaranteed ROI targets, reply here and I will share the Notion breakdown. Happy to answer any questions you may have.

Best regards,
AsyncFlow Systems""",
        "email_step1_5_followup": """Hi Oliver,

Just following up on this — our modular Staging Sandbox architecture validates workflow changes in complete isolation (0% risk of breaking production ERP or ledgers), backed by a contractual guarantee to identify at least $20,000 in annual operational waste.

Happy to answer any questions you may have.

Best regards,
AsyncFlow Systems""",
        "notion_adaptation_blueprint": """# Apex Settlement Labs — Asynchronous Webhook Settlement Architecture

### 1. Executive Summary & Industry Problem X
At high-volume Open Banking throughput, delayed or dropped webhook retries across UK & European banking APIs create accounting desynchronization, costing up to €320,000 annually in manual engineering triage and ledger auditing.

### 2. Modular Architecture & Staging Sandbox (25-Line Python Skeleton)
```python
import hashlib
from typing import Dict, Any
from pydantic import BaseModel, Field

class SettlementEvent(BaseModel):
    event_id: str
    merchant_id: str
    amount_cents: int
    clearing_scheme: str  # Faster Payments / BACS / SEPA
    idempotency_hash: str = Field(default="")

    def compute_hash(self) -> str:
        payload = f"{self.event_id}:{self.merchant_id}:{self.amount_cents}"
        return hashlib.sha256(payload.encode()).hexdigest()

class StagingReconciler:
    def __init__(self, db_client):
        self.db = db_client

    async def verify_and_commit(self, event: SettlementEvent) -> Dict[str, Any]:
        event.idempotency_hash = event.compute_hash()
        exists = await self.db.check_hash(event.idempotency_hash)
        if exists:
            return {"status": "skipped", "reason": "idempotent_duplicate"}
        await self.db.record_staged_transaction(event.model_dump())
        return {"status": "verified", "hash": event.idempotency_hash}
```

### 3. 5-Day Zero-Meeting Audit & Adaptation SOW ($2,000)
- Day 1: Async Intake (15-min Loom walkthrough of webhook retry logs & DPA signing).
- Day 2-3: Idempotency queue audit & dead-letter bottleneck mapping.
- Day 4: Mathematical ROI modeling ($20,000+ benchmark calculation).
- Day 5: Delivery of complete PRD + executable code repository in Notion.

### 4. Contractual 10x ROI Guarantee
If this audit does not identify at least $20,000 in provable annual labor and error waste reduction, 100% of the $2,000 fee is refunded immediately.

### 5. Enterprise Security & GDPR DPA
- 100% Zero-Public LLM Training: All logic executes deterministically on private infrastructure.
- Standardized European GDPR Data Processing Agreement (DPA) signed prior to intake.

### 6. Dual Payment Gate
- **Option A (Stripe Checkout):** $2,000 instant card payment with automated Notion workspace access.
- **Option B (SEPA B2B Invoice):** Official B2B invoice with corporate IBAN and European VAT Reverse Charge.""",
        "status": "Не відправлено"
    },
    {
        "inbox_slot": "Пошта 1",
        "company": "Vanguard Cargo Logistics GmbH",
        "country": "🇩🇪 Німеччина (Berlin)",
        "website": "vanguard-cargo.example.de",
        "industry_problem_x": "Ручний аудит інвойсів 3PL-перевізників на відповідність погодженим тарифним сіткам, паливним надбавкам та демередж-вікнам.",
        "contact_role": "Maximilian Weber (Chief Operating Officer)",
        "verified_email": "m.weber@vanguard-cargo.example.de",
        "mx_status": "Verified MX (Microsoft 365) + HTTP 200 Live",
        "email_step1_plain_text": """Subject: Vanguard Cargo carrier invoice surcharge reconciliation

Hi Maximilian,

In scalable logistics networks, reconciling monthly carrier billing against contracted rate cards is a persistent drain: dynamic fuel surcharges and dimensional weight re-ratings create billing discrepancies and manual audit delays.

We designed a modular rate-audit staging pipeline that deterministically validates carrier line items against contracted tariffs with zero ERP risk. The system adapts asynchronously without meetings.

If an async audit of this workflow with verified ROI figures sounds useful, reply here and I will share the Notion overview. Happy to answer any questions you may have.

Best regards,
AsyncFlow Systems""",
        "email_step1_5_followup": """Hi Maximilian,

Just following up on this — our modular Staging Sandbox architecture validates workflow changes in complete isolation (0% risk of breaking production ERP or ledgers), backed by a contractual guarantee to identify at least $20,000 in annual operational waste.

Happy to answer any questions you may have.

Best regards,
AsyncFlow Systems""",
        "notion_adaptation_blueprint": """# Vanguard Cargo Logistics — Carrier Invoice & Surcharge Reconciliation

### 1. Executive Summary & Industry Problem X
Carrier invoice discrepancy rates average 4.2% of total freight spend due to unverified fuel surcharges and accessorial charges, totaling €210,000 in unchecked overpayments annually.

### 2. Modular Architecture & Staging Sandbox (25-Line Python Skeleton)
```python
from typing import Dict, Any
from pydantic import BaseModel

class CarrierInvoiceLine(BaseModel):
    tracking_code: str
    billed_weight_kg: float
    billed_total: float
    carrier_id: str

class TariffRule(BaseModel):
    base_per_kg: float
    fuel_surcharge_pct: float

class FreightAuditor:
    def audit_line(self, line: CarrierInvoiceLine, rule: TariffRule) -> Dict[str, Any]:
        expected_base = line.billed_weight_kg * rule.base_per_kg
        expected_total = expected_base * (1.0 + rule.fuel_surcharge_pct / 100.0)
        discrepancy = line.billed_total - expected_total
        return {
            "tracking": line.tracking_code,
            "discrepancy": round(discrepancy, 2),
            "flagged": discrepancy > 5.0,
            "audit_status": "disputed" if discrepancy > 5.0 else "approved"
        }
```

### 3. 5-Day Zero-Meeting Audit & Adaptation SOW ($2,000)
- Day 1: Async Intake (Loom walkthrough of carrier invoice formats).
- Day 2-3: Tariff rule engine specification & tolerance mapping.
- Day 4: ROI quantification ($20,000+ benchmark).
- Day 5: Delivery of Notion architecture & executable Python code.

### 4. Contractual 10x ROI Guarantee
Full refund of $2,000 if less than $20,000 in verifiable annual savings is identified.

### 5. Enterprise Security & GDPR DPA
Isolated deterministic processing; zero data leakage; GDPR enterprise agreement.

### 6. Dual Payment Gate
- **Option A (Stripe Checkout):** $2,000 corporate card payment with instant Notion workspace access.
- **Option B (SEPA B2B Invoice):** Official B2B invoice with corporate IBAN and European VAT Reverse Charge.""",
        "status": "Відправлено"
    },
    {
        "inbox_slot": "Пошта 2",
        "company": "NovaFlow Intelligence Ltd",
        "country": "🇺🇦 Україна (Kyiv)",
        "website": "novaflow.example.ua",
        "industry_problem_x": "Розсинхрон між подіями підписок у платіжній системі та правами доступу користувачів у внутрішній CRM/базі даних клієнтів.",
        "contact_role": "Maksym Boyko (VP of Product Engineering)",
        "verified_email": "maksym@novaflow.example.ua",
        "mx_status": "Verified MX (Google Workspace) + HTTP 200 Live",
        "email_step1_plain_text": """Subject: NovaFlow subscription billing and CRM sync

Hi Maksym,

In growing B2B SaaS platforms, subscription plan transitions and pro-rated upgrade webhooks frequently desynchronize from customer access permissions in internal CRM databases, forcing support engineers into manual database fixups.

We built an isolated staging module that validates and normalizes subscription events before CRM write commits, ensuring 100% entitlement accuracy with zero lock risk. The solution adapts asynchronously without meetings.

If an async audit of this workflow with hard ROI targets sounds valuable, drop a reply and I will share the Notion blueprint. Happy to answer any questions you may have.

Best regards,
AsyncFlow Systems""",
        "email_step1_5_followup": """Hi Maksym,

Just following up on this — our modular Staging Sandbox architecture validates workflow changes in complete isolation (0% risk of breaking production ERP or ledgers), backed by a contractual guarantee to identify at least $20,000 in annual operational waste.

Happy to answer any questions you may have.

Best regards,
AsyncFlow Systems""",
        "notion_adaptation_blueprint": """# NovaFlow Intelligence — Subscription Event & CRM Entitlement Sync

### 1. Executive Summary & Industry Problem X
Desynchronization between billing webhooks and customer account entitlements causes service access discrepancies across 6% of mid-tier clients, producing €140,000 in customer churn and engineering support overhead.

### 2. Modular Architecture & Staging Sandbox (25-Line Python Skeleton)
```python
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel

class SubscriptionDelta(BaseModel):
    account_id: str
    plan_tier: str
    seats_allocated: int
    renews_at: datetime
    is_active: bool

class EntitlementStagingPipeline:
    def __init__(self, crm_client):
        self.crm = crm_client

    async def stage_entitlement_update(self, delta: SubscriptionDelta) -> Dict[str, Any]:
        if delta.seats_allocated < 1:
            return {"status": "rejected", "reason": "invalid_seats"}
        staged_record = {
            "account_id": delta.account_id,
            "tier": delta.plan_tier,
            "seats": delta.seats_allocated,
            "staged_at": datetime.utcnow().isoformat()
        }
        await self.crm.commit_staged_entitlement(staged_record)
        return {"status": "promoted", "account_id": delta.account_id}
```

### 3. 5-Day Zero-Meeting Audit & Adaptation SOW ($2,000)
- Day 1: Async Intake (Loom review of webhook event schemas).
- Day 2-3: Staging schema mapping & state machine validation.
- Day 4: Quantified ROI modeling ($20,000+ benchmark).
- Day 5: Delivery of Notion architecture & executable Python code.

### 4. Contractual 10x ROI Guarantee
100% refund of $2,000 fee if at least $20,000 in annual savings is not demonstrated.

### 5. Enterprise Security & GDPR DPA
Zero public LLM exposure; air-gapped deterministic validation; GDPR compliant.

### 6. Dual Payment Gate
- **Option A (Stripe Checkout):** $2,000 corporate card payment with instant Notion workspace access.
- **Option B (SEPA B2B Invoice):** Official B2B invoice with corporate IBAN and European VAT Reverse Charge.""",
        "status": "Отримано відповідь"
    }
]

def seed_demo_data(target_db: str = DB_FILE, reset: bool = False) -> int:
    """Populates SQLite database with 3 fictitious companies for demo & screenshots."""
    if reset and os.path.exists(target_db):
        os.remove(target_db)
        print(f"[RESET] Cleared database at {target_db}")

    init_db(target_db)

    # Check if demo data or leads already present
    existing = get_leads(db_path=target_db)
    if existing and not reset:
        print(f"[INFO] Database already contains {len(existing)} leads. Skipping seed (use --reset to re-seed).")
        return len(existing)

    inserted_count = 0
    for company in DEMO_COMPANIES:
        lead_id = insert_lead(company, db_path=target_db)
        inserted_count += 1
        words = len(company["email_step1_plain_text"].split())
        print(f"[INSERTED] #{lead_id} | {company['company']} ({company['country']}) | Words: {words} | Status: {company['status']}")

    metrics = count_metrics(db_path=target_db)
    print(f"\n[SUCCESS] Successfully seeded {inserted_count} demo companies into {target_db}!")
    print(f"Metrics: Total={metrics['total']}, Inbox 1={metrics['inbox_1']}, Inbox 2={metrics['inbox_2']}, Verified={metrics['verified']}")
    return inserted_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed safe demo data for live UI testing and screenshots.")
    parser.add_argument("--reset", action="store_true", help="Wipe existing database before seeding.")
    parser.add_argument("--db", type=str, default=DB_FILE, help="Custom SQLite database path.")
    args = parser.parse_args()

    seed_demo_data(target_db=args.db, reset=args.reset)
