"""
Core Architecture Blueprint Generator for Async B2B Consulting.
Based on the Google Cloud Solution Architecture workflow standard.
Generates comprehensive 1-page architecture solution blueprints, interactive HTML presentations
with Mermaid diagrams, and email reply snippets for qualified SMB prospects.
"""

import os
import base64
from typing import Dict, Any

class ArchitectureBlueprintGenerator:
    def __init__(self, output_dir: str = "data/blueprints"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_email_reply(self, account: Dict[str, Any]) -> str:
        """
        Генерує супровідний лист-відповідь англійською мовою (US Business English)
        для випадку, коли ЛПР відповідає: 'Yes, send it over'.
        """
        name = account.get("name", "there")
        dm = account.get("decision_maker", {})
        first_name = dm.get("first_name") or dm.get("full_name", "").split()[0] or "there"
        domain = account.get("domain", "")
        bottleneck = account.get("process_bottleneck_hypothesis", "operational synchronization")

        return (
            f"Hi {first_name},\n\n"
            f"Thanks for getting back to me. As promised, I've outlined the 1-page architecture blueprint below for {name}.\n\n"
            f"This breakdown is based on the benchmark architecture we use for peer companies at your scale (20–70 people) "
            f"to eliminate manual spreadsheet reconciliation and desync bottlenecks without adding headcount.\n\n"
            f"We designed this to be 100% async: if any edge case in your current stack differs from this benchmark, "
            f"simply reply with a quick note and I'll calibrate the architecture specifically for your setup at no cost.\n\n"
            f"Hope this gives you clear clarity on the flow. Let me know what you think!\n\n"
            f"Best regards,\n"
            f"[Your Name]\n"
            f"Independent Process Automation Consultant\n"
            f"[Your Portfolio / LinkedIn]"
        )

    def generate_blueprint_markdown(self, account: Dict[str, Any]) -> str:
        """
        Генерує детальний 1-сторінковий архітектурний блюпринт у форматі Markdown
        за методологією Google Cloud Solution Architecture.
        """
        acc_id = account.get("id", "acc-unknown")
        name = account.get("name", "Target Company")
        domain = account.get("domain", "")
        industry = account.get("industry", "Technology")
        size = account.get("size", "25-50 employees")
        hq = account.get("headquarters", "United States")
        dm = account.get("decision_maker", {})
        dm_name = dm.get("full_name", "Leadership Team")
        dm_title = dm.get("title", "Executive")
        bottleneck = account.get("process_bottleneck_hypothesis", "")
        trigger = account.get("operational_pain_trigger", "")

        # Формування кастомних компонентів під індустрію
        mermaid_diagram = self._build_mermaid_diagram(account)
        encoded_mermaid = base64.urlsafe_b64encode(mermaid_diagram.encode("utf-8")).decode("utf-8")
        diagram_image_url = f"https://mermaid.ink/img/{encoded_mermaid}"
        tech_specs = self._build_technical_specs(account)
        roi_metrics = self._build_roi_metrics(account)

        md = f"""# 📐 Architecture Solution Blueprint: {name}
**Prepared for:** {dm_name} ({dm_title})  
**Domain:** [{domain}](https://{domain}) | **Scale:** {size} | **HQ:** {hq}  
**Architecture Spec ID:** `ARCH-{acc_id.upper()}-2026`  
**Methodology:** Google Cloud Solution Architecture & Async Event-Driven Automation  

---

> [!NOTE]
> **Executive Summary & Industry Benchmark Context**  
> Fast-growing organizations scaling between 20 and 80 team members typically hit a structural friction point: while revenue expands rapidly, core operational pipelines rely on manual cross-system checks.  
> **Identified Industry Pattern:** *{bottleneck}*  
> **Key Operational Trigger:** *{trigger}*  
> This blueprint details an event-driven, self-healing automation architecture designed to eliminate status meetings and manual spreadsheet handoffs entirely.

---

## 1. 🏗️ Target System Architecture

![Target Architecture Blueprint]({diagram_image_url})

---

## 2. ⚙️ Component Breakdown & Data Flow

{tech_specs}

---

## 3. 📊 Projected Business Impact & ROI

{roi_metrics}

---

## 4. 🚀 2-Week Async Implementation Roadmap (Zero Meetings)

We operate with a strict **Zero-Meeting / 100% Async Policy**. Execution is coordinated entirely via private Slack Connect channels, documented Notion specifications, and automated pull requests.

| Phase | Timeline | Async Deliverables & Milestones | Time Required from Your Team |
| :--- | :---: | :--- | :---: |
| **Phase 1: Calibration & Schema Mapping** | Days 1–3 | Exchange API tokens, map data schemas, and document custom edge cases in a shared Notion workspace. | < 30 mins (Text review) |
| **Phase 2: Event Pipeline & Dry-Run** | Days 4–8 | Provision isolated cloud workers, build idempotent queues, and run parallel shadow reconciliation without mutating live production data. | 0 mins |
| **Phase 3: Production Cutover & Slack Audit** | Days 9–14 | Enable live automated routing, activate real-time Slack exception notifications, and verify error-free runs. | 15 mins (Signoff) |

---

## 5. 🛡️ Security, Privacy & Compliance Standard

* **Zero Data Retention (ZDR):** Payloads are processed in-flight with end-to-end TLS 1.3 encryption; customer PII is never permanently stored on external middleware.
* **SOC2 & GDPR Alignment:** All workers run in isolated single-tenant cloud functions with least-privilege IAM roles.
* **Auditability:** Every transaction logs a cryptographically verifiable SHA-256 hash to your private Slack ops audit channel.

---

> [!TIP]
> **Custom Adaptation Note for {name}:**  
> This document outlines our proven benchmark pattern. If your internal edge cases, custom ERP, or warehouse workflows differ from this design, we can calibrate this architecture specifically to your exact business stack in 48 hours—entirely asynchronously.  
> **Contact:** Simply reply to our email with your questions or notes.
"""
        return md.strip()

    def generate_blueprint_html(self, account: Dict[str, Any], markdown_content: str) -> str:
        """
        Генерує автономний красивий HTML-файл з підтримкою Mermaid.js,
        Google Font (Inter), акуратними бейджами та адаптацією під друк/PDF.
        """
        name = account.get("name", "Company")
        domain = account.get("domain", "")
        dm = account.get("decision_maker", {})
        dm_name = dm.get("full_name", "Executive")
        dm_title = dm.get("title", "")
        mermaid_code = self._build_mermaid_diagram(account)

        # Конвертація базових елементів або підготовка красивого HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Architecture Solution Blueprint — {name} ({domain})</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({{ startOnLoad: true, theme: 'neutral', securityLevel: 'loose' }});
  </script>
  <style>
    :root {{
      --primary: #4F46E5;
      --primary-light: #EEF2FF;
      --success: #059669;
      --success-light: #ECFDF5;
      --warning: #D97706;
      --warning-light: #FFFBEB;
      --text-main: #111827;
      --text-muted: #4B5563;
      --border: #E5E7EB;
      --card-bg: #FFFFFF;
      --bg: #F9FAFB;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text-main);
      line-height: 1.6;
      padding: 40px 20px;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 48px;
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
    }}
    .header {{
      border-bottom: 2px solid var(--border);
      padding-bottom: 24px;
      margin-bottom: 32px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }}
    .header-title h1 {{
      font-size: 26px;
      font-weight: 800;
      color: #111827;
      letter-spacing: -0.02em;
      margin-bottom: 6px;
    }}
    .header-meta {{
      font-size: 14px;
      color: var(--text-muted);
    }}
    .header-meta strong {{
      color: var(--text-main);
    }}
    .badge {{
      display: inline-block;
      padding: 6px 12px;
      background: var(--primary-light);
      color: var(--primary);
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .callout {{
      background: var(--primary-light);
      border-left: 4px solid var(--primary);
      padding: 16px 20px;
      border-radius: 8px;
      margin-bottom: 32px;
    }}
    .callout h3 {{
      font-size: 15px;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 4px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .callout p {{
      font-size: 14px;
      color: #374151;
    }}
    h2 {{
      font-size: 20px;
      font-weight: 700;
      color: #111827;
      margin: 32px 0 16px 0;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .diagram-container {{
      background: #F8FAFC;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      margin: 20px 0;
      text-align: center;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin: 16px 0;
    }}
    .card {{
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px;
    }}
    .card h4 {{
      font-size: 15px;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 8px;
    }}
    .card p {{
      font-size: 13px;
      color: var(--text-muted);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      font-size: 14px;
    }}
    th, td {{
      padding: 12px 14px;
      border: 1px solid var(--border);
      text-align: left;
    }}
    th {{
      background: #F3F4F6;
      font-weight: 600;
      color: #374151;
    }}
    .roi-box {{
      background: var(--success-light);
      border: 1px solid #A7F3D0;
      border-radius: 12px;
      padding: 20px;
      margin: 24px 0;
    }}
    .roi-box h3 {{
      color: var(--success);
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 8px;
    }}
    .adaptation-box {{
      background: var(--warning-light);
      border: 1px solid #FDE68A;
      border-radius: 12px;
      padding: 20px;
      margin-top: 36px;
    }}
    .adaptation-box h3 {{
      color: var(--warning);
      font-size: 16px;
      font-weight: 700;
      margin-bottom: 6px;
    }}
    .adaptation-box p {{
      font-size: 13.5px;
      color: #78350F;
    }}
    .footer-actions {{
      margin-top: 36px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 24px;
      border-top: 1px solid var(--border);
    }}
    .print-btn {{
      background: var(--primary);
      color: #FFFFFF;
      padding: 10px 20px;
      border-radius: 8px;
      text-decoration: none;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    @media print {{
      body {{ background: #FFF; padding: 0; }}
      .container {{ border: none; box-shadow: none; padding: 0; max-width: 100%; }}
      .footer-actions {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-title">
        <span class="badge">Google Cloud Solution Architecture</span>
        <h1 style="margin-top: 8px;">Architecture Blueprint: {name}</h1>
        <div class="header-meta">
          Target Executive: <strong>{dm_name}</strong> ({dm_title}) &bull; Target Domain: <strong>{domain}</strong>
        </div>
      </div>
      <div>
        <button class="print-btn" onclick="window.print()">🖨️ Export to PDF</button>
      </div>
    </div>

    <div class="callout">
      <h3>Executive Benchmark Summary</h3>
      <p>
        <strong>Observed Friction Point:</strong> {account.get("process_bottleneck_hypothesis", "")}<br>
        <strong>Industry Trigger:</strong> {account.get("operational_pain_trigger", "")}
      </p>
    </div>

    <h2>1. Target Event-Driven Architecture</h2>
    <div class="diagram-container">
      <div class="mermaid">
{mermaid_code}
      </div>
    </div>

    <h2>2. Technical Component Breakdown</h2>
    <div class="grid-2">
      <div class="card">
        <h4>1. Ingestion & Webhook Layer</h4>
        <p>Receives webhook event payloads securely with HMAC signature verification, zero latency, and automatic retry queues.</p>
      </div>
      <div class="card">
        <h4>2. Cloud Event Buffer (Idempotent)</h4>
        <p>Guarantees strict FIFO processing and deduplication, preventing double-processing during spike events or network blips.</p>
      </div>
      <div class="card">
        <h4>3. Async Reconciliation Engine</h4>
        <p>Stateless micro-worker reconciles business rules, matches stock/invoices/tickets, and applies deterministic business logic.</p>
      </div>
      <div class="card">
        <h4>4. Destination Sync & Slack Audit</h4>
        <p>Atomically synchronizes data back into core destinations and broadcasts real-time anomaly alerts to private ops channels.</p>
      </div>
    </div>

    <h2>3. Quantified Business Impact & ROI</h2>
    <div class="roi-box">
      <h3>Expected Operational Gains (Validated Benchmark):</h3>
      <p>
        &bull; <strong>Time Savings:</strong> 20 to 30 hours per week of manual spreadsheet triage eliminated.<br>
        &bull; <strong>OPEX Reduction:</strong> 40%–60% reduction in customer support / ops overhead without hiring additional coordinators.<br>
        &bull; <strong>Error Rate:</strong> 99.8% reduction in manual data entry desync, stockouts, or disputed invoices.<br>
        &bull; <strong>SLA Latency:</strong> Process turnaround reduced from 24–48 hours to &lt; 3 seconds real-time.
      </p>
    </div>

    <h2>4. 2-Week Async Implementation Roadmap (Zero Meetings)</h2>
    <table>
      <thead>
        <tr>
          <th>Phase</th>
          <th>Timeline</th>
          <th>Deliverable & Scope</th>
          <th>Client Time</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>1. Calibration & Setup</strong></td>
          <td>Days 1–3</td>
          <td>API token handshake, schema validation, Notion project kick-off.</td>
          <td>&lt; 30 mins (Text review)</td>
        </tr>
        <tr>
          <td><strong>2. Pipeline & Dry Run</strong></td>
          <td>Days 4–8</td>
          <td>Deploy serverless workers, run parallel shadow reconciliation.</td>
          <td>0 mins</td>
        </tr>
        <tr>
          <td><strong>3. Cutover & Slack Alerts</strong></td>
          <td>Days 9–14</td>
          <td>Live routing cutover, automated Slack audit trail activated.</td>
          <td>15 mins (Signoff)</td>
        </tr>
      </tbody>
    </table>

    <div class="adaptation-box">
      <h3>Need a Tailored Customization for {name}?</h3>
      <p>
        This blueprint represents our proven benchmark pattern for high-growth operations. If your internal tech stack, 
        warehouse nodes, or custom rules differ from this design, <strong>we adapt this architecture specifically to your exact workflows in 48 hours—100% asynchronously with zero meetings</strong>.
      </p>
    </div>

    <div class="footer-actions">
      <span style="font-size: 13px; color: var(--text-muted);">
        Confidential &bull; Prepared exclusively for {name} ({domain})
      </span>
      <button class="print-btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
    </div>
  </div>
</body>
</html>
"""
        return html

    def save_all_blueprints_for_lead(self, account: Dict[str, Any]) -> Dict[str, str]:
        """
        Генерує та зберігає як Markdown (.md), так і стилізований HTML (.html).
        Повертає шляхи до збережених файлів.
        """
        acc_id = account.get("id", "acc-unknown")
        md_content = self.generate_blueprint_markdown(account)
        html_content = self.generate_blueprint_html(account, md_content)
        email_reply = self.generate_email_reply(account)

        md_path = os.path.join(self.output_dir, f"{acc_id}.md")
        html_path = os.path.join(self.output_dir, f"{acc_id}.html")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return {
            "blueprint_path_md": md_path,
            "blueprint_path_html": html_path,
            "blueprint_summary": account.get("process_bottleneck_hypothesis", ""),
            "email_reply_template": email_reply
        }

    def _build_mermaid_diagram(self, account: Dict[str, Any]) -> str:
        """
        Будує специфічну візуальну діаграму Mermaid залежно від галузі та проблеми компанії.
        """
        domain = account.get("domain", "")
        name = account.get("name", "Company")

        if "lunya" in domain:
            return """flowchart LR
    Shopify["Shopify Plus (Preorders & Core Drops)"] -->|Webhook Event| Queue["Cloud Pub/Sub (FIFO Buffer)"]
    EDI["Wholesale EDI (Department Stores)"] -->|Batch Ingestion| Queue
    Queue --> Worker["Async Allocation Engine (Rules & Stock Match)"]
    Worker --> HubA["3PL Primary Hub (East Coast)"]
    Worker --> HubB["3PL Secondary Hub (West Coast)"]
    Worker -->|Exception / Stockout Alert| Slack["Slack Ops Channel (#lunya-dispatch)"]
    classDef highlight fill:#4F46E5,stroke:#312E81,stroke-width:2px,color:#fff;
    class Worker highlight;"""

        elif "chamberlain" in domain:
            return """flowchart LR
    Recharge["Recharge Subscriptions (Recurring Surges)"] -->|Webhook Trigger| Broker["Cloud Event Buffer (Idempotent)"]
    Retail["Retail Orders (National Chains)"] -->|Inventory Hold| Broker
    Broker --> Engine["Dynamic Replenishment Engine"]
    Engine --> WMS["Warehouse WMS (Automated Wave Picking)"]
    Engine -->|Backorder Warning| Alert["Slack Fulfillment (#chamberlain-replenishment)"]
    classDef highlight fill:#059669,stroke:#065F46,stroke-width:2px,color:#fff;
    class Engine highlight;"""

        elif "finisterre" in domain:
            return """flowchart LR
    Zendesk["Zendesk Support (Warranty / Repairs Intake)"] -->|Ticket Webhook| Ingest["Automated Intake Worker"]
    Shopify["Shopify Inventory"] <-->|Spares & Materials Sync| Ingest
    Ingest --> Workshop["Warranty Workshop Queue (Kanban Routing)"]
    Ingest --> Customs["EU/UK Customs Export Agent (Automated Docs)"]
    Ingest -->|Status Sync| Customer["Automated Customer SMS / Email Notifications"]
    classDef highlight fill:#D97706,stroke:#78350F,stroke-width:2px,color:#fff;
    class Ingest highlight;"""

        elif "dame" in domain:
            return """flowchart LR
    Creator["Affiliate & Creator Channels (TikTok / IG)"] -->|Referral Links & Codes| Tracker["Attribution Ingestion Layer"]
    Shopify["Shopify Plus Sales"] -->|Order Completed| Tracker
    Tracker --> Reconcile["Commission Reconciliation Worker"]
    Reconcile --> Payouts["Automated Payouts API (Wise / Stripe Connect)"]
    Reconcile -->|Discrepancy / Fraud Flag| Slack["Slack Marketing Ops Channel"]
    classDef highlight fill:#EC4899,stroke:#831843,stroke-width:2px,color:#fff;
    class Reconcile highlight;"""

        elif "freightclub" in domain:
            return """flowchart LR
    Carrier["LTL Regional Carriers (Invoices / EDI 210)"] -->|Raw Invoice Intake| Ingest["Invoice Parser & OCR Agent"]
    BOL["Original BOL / Quotes Database"] -->|Rate Verification| Ingest
    Ingest --> Audit["Dispute & Accessorial Fee Auditor"]
    Audit -->|Matched / Approved| ERP["NetSuite / AP Accounting (Auto-Approve)"]
    Audit -->|Overcharge Detected| Dispute["Auto-Dispute Generator (Instant Carrier Claim)"]
    classDef highlight fill:#2563EB,stroke:#1E40AF,stroke-width:2px,color:#fff;
    class Audit highlight;"""

        elif "airspace" in domain:
            return """flowchart LR
    Airlines["Commercial Airline Flight Telemetry"] -->|Schedule Shift Webhook| Event["Urgent Dispatch Event Broker"]
    Driver["Active Ground Couriers (Driver GPS)"] -->|Live Geolocation| Event
    Event --> Reroute["Dynamic Courier Re-Routing Engine"]
    Reroute --> SMS["Push Notification / Instant Turn-by-Turn Re-routing"]
    Reroute --> SLA["Critical SLA Monitor (< 15 min Organ Transfer)"]
    classDef highlight fill:#DC2626,stroke:#991B1B,stroke-width:2px,color:#fff;
    class Reroute highlight;"""

        elif "huboo" in domain:
            return """flowchart LR
    Store["Client Stores (Amazon / Shopify / TikTok)"] -->|Real-Time Orders| Router["Micro-Hub Routing Queue"]
    HubUK["UK Micro-Hubs"] <-->|Stock Level Telemetry| Balancer["Replenishment Balancer"]
    HubEU["EU Micro-Hubs"] <-->|Stock Level Telemetry| Balancer
    Balancer --> Transfer["Automated Inter-Hub Transfer Orders"]
    Balancer --> Customs["Post-Brexit Automated Transit Declaration Agent"]
    classDef highlight fill:#0284C7,stroke:#0369A1,stroke-width:2px,color:#fff;
    class Balancer highlight;"""

        elif "missive" in domain:
            return """flowchart LR
    Email["Missive Shared Inboxes (Team Conversations)"] -->|Webhook Stream| Ingest["Schema Validation Buffer"]
    CRMs["Client CRMs (HubSpot / Salesforce / Pipedrive)"] <--> Ingest
    Ingest --> Worker["Self-Healing Sync Worker (Schema Drift Shield)"]
    Worker -->|Auto-Retry & Deduplication| DeadLetter["Dead-Letter Queue & Slack Alert"]
    Worker -->|Synced Context| MissiveThread["Missive Sidebar Context Widget"]
    classDef highlight fill:#8B5CF6,stroke:#5B21B6,stroke-width:2px,color:#fff;
    class Worker highlight;"""

        elif "june" in domain:
            return """flowchart LR
    Telemetry["Product Telemetry Events (Segment / June SDK)"] -->|Event Stream| Ingestion["High-Throughput Metering Worker"]
    Stripe["Stripe Customer Usage Tiers"] <--> Ingestion
    Ingestion --> Reconcile["Metered Overage Calculator"]
    Reconcile -->|Usage Threshold Breached| Provisioning["Automated Tier Provisioning & Invoice Sync"]
    Reconcile --> CS["Customer Success Slack Alert (Expansion Trigger)"]
    classDef highlight fill:#F59E0B,stroke:#B45309,stroke-width:2px,color:#fff;
    class Reconcile highlight;"""

        else: # plain.com
            return """flowchart LR
    Slack["Enterprise Customer Slack Connect Channels"] -->|Discussion Webhook| Ingest["Triage & Context Parser"]
    Linear["Linear / GitHub Issue Tracker"] <--> Ingest
    Ingest --> Engine["Bi-Directional Sync & Deduplication Engine"]
    Engine --> Thread["Live Status Reply back to Customer Slack Thread"]
    Engine --> Metrics["SLA Resolution Time Tracker"]
    classDef highlight fill:#10B981,stroke:#047857,stroke-width:2px,color:#fff;
    class Engine highlight;"""

    def _build_technical_specs(self, account: Dict[str, Any]) -> str:
        domain = account.get("domain", "")
        if "lunya" in domain:
            return """* **1. Ingestion Layer:** Event webhooks from Shopify Plus captured via Google Cloud Functions with zero latency.
* **2. FIFO Queue:** Cloud Pub/Sub guarantees sequential delivery of preorder batches, preventing race conditions across inventory pools.
* **3. Reconciliation Logic:** Real-time lookup against 3PL warehouse node capacities; allocates stock closest to customer zip codes.
* **4. Fallback & Notification:** Automatic Slack notification if inventory dips below threshold; zero spreadsheet overrides."""
        elif "chamberlain" in domain:
            return """* **1. Subscription Batcher:** Groups recurring Recharge charges into synchronized warehouse picking waves.
* **2. Buffer Layer:** Absorbs peak renewal surges (e.g. 1st and 15th of month) without overwhelming WMS API rate limits.
* **3. Inventory Protection:** Locks physical stock for subscription loyalty members before allocating to wholesale channels.
* **4. Slack Alerting:** Real-time visibility into SKU fulfillment bottlenecks."""
        elif "freightclub" in domain:
            return """* **1. Invoice Ingestion:** Automated webhook/EDI parser extracts line-item accessorial charges from carrier invoices.
* **2. Reconciliation Rules:** Automatically matches freight bills against original BOL quotes and tolerances.
* **3. Auto-Approval:** 90%+ of clean invoices routed straight into accounting with zero human touch.
* **4. Dispute Engine:** Instant dispute packet generated and emailed back to carrier for unauthorized surcharges."""
        elif "plain" in domain:
            return """* **1. Slack Connect Listener:** Filters noise and captures bug reports and support requests directly from enterprise channels.
* **2. AI Deduplication:** Matches incoming messages against existing Linear/GitHub issues to prevent duplicate work.
* **3. Bi-Directional Bridge:** When engineering moves a Linear ticket to 'Done', the Slack thread is automatically updated with resolution context.
* **4. SLA Telemetry:** Tracks customer wait times without manual spreadsheet tracking."""
        else:
            return """* **1. Event Ingestion:** Captures inbound webhooks with HMAC signature verification and sub-millisecond response.
* **2. State Reconciliation Engine:** Reconciles disparate data schemas between core systems automatically.
* **3. Idempotent Cloud Queue:** Eliminates race conditions, ensuring zero duplicate transactions.
* **4. Audit & Alerting:** Comprehensive transaction logs and Slack exception alerts for operations visibility."""

    def _build_roi_metrics(self, account: Dict[str, Any]) -> str:
        return """| Target Metric | Baseline (Current Manual Process) | Target Architecture (Automated) | Projected Gain / ROI |
| :--- | :---: | :---: | :---: |
| **Manual Labor Overhead** | 20–30 hours/week in spreadsheets | &lt; 1 hour/week (Exceptions only) | **~25 hrs/week saved** |
| **Order / Sync Latency** | 12 to 36 hours delay | &lt; 3 seconds real-time | **99.9% faster turnaround** |
| **Error & Stockout Rate** | 3.5%–7.0% discrepancy rate | 0.05% (Deterministic validation) | **Eliminates costly chargebacks** |
| **Implementation Footprint** | 3–6 months heavy internal IT project | 2 weeks pure async integration | **Zero status meetings** |"""

