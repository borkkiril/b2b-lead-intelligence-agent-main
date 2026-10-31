"""
Notion Publisher Module.
Publishes 1-page Architecture Solution Blueprints directly to the user's Notion workspace
via the official Notion REST API.
Enables instant access from mobile devices (Notion iOS / Android app) and one-click sharing with clients.
"""

import os
import json
import time
import base64
import requests
from typing import Dict, Any, List, Optional
from core.architecture_blueprint_generator import ArchitectureBlueprintGenerator

class NotionPublisher:
    def __init__(self, token: Optional[str] = None, parent_page_id: Optional[str] = None):
        # Зчитування токена з параметрів або з .env
        self.token = token or os.getenv("NOTION_TOKEN")
        self.parent_page_id = parent_page_id or os.getenv("NOTION_PARENT_PAGE_ID")
        self.api_version = "2022-06-28"
        self.base_url = "https://api.notion.com/v1"
        self.generator = ArchitectureBlueprintGenerator()

        # Якщо токен не знайдено в os.environ, пробуємо прочитати з файлу .env вручну
        if not self.token or not self.parent_page_id:
            self._load_from_dotenv()

    def _load_from_dotenv(self):
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("NOTION_TOKEN="):
                        self.token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("NOTION_PARENT_PAGE_ID="):
                        self.parent_page_id = line.split("=", 1)[1].strip().strip('"').strip("'")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.api_version,
            "Content-Type": "application/json"
        }

    def test_connection(self) -> Dict[str, Any]:
        """
        Перевіряє доступність Notion API та знаходить доступні сторінки/бази.
        """
        if not self.token:
            return {"success": False, "error": "NOTION_TOKEN не налаштовано."}

        try:
            res = requests.post(
                f"{self.base_url}/search",
                headers=self._get_headers(),
                json={},
                timeout=15
            )
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                return {
                    "success": True,
                    "results_count": len(results),
                    "pages": [
                        {
                            "id": r.get("id"),
                            "object": r.get("object"),
                            "url": r.get("url"),
                            "title": self._extract_title(r)
                        }
                        for r in results
                    ]
                }
            else:
                return {
                    "success": False,
                    "status_code": res.status_code,
                    "error": res.text
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _extract_title(self, item: Dict[str, Any]) -> str:
        props = item.get("properties", {})
        for p_name, p_val in props.items():
            if isinstance(p_val, dict) and p_val.get("type") == "title":
                t_list = p_val.get("title", [])
                if t_list:
                    return "".join([t.get("plain_text", "") for t in t_list])
        title_list = item.get("title", [])
        if title_list:
            return "".join([t.get("plain_text", "") for t in title_list])
        return "Untitled"

    def build_notion_blocks(self, account: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Формує валідні блоки Notion для архітектурного рішення:
        - Callout з бенчмарком
        - Code block з мовою Mermaid (Notion рендерить діаграми нативно)
        - Компоненти та специфікації
        - Таблиця / Callout з ROI
        - 2-тижневий асинхронний план
        - Готовий текст листа-відповіді
        """
        name = account.get("name", "Company")
        domain = account.get("domain", "")
        dm = account.get("decision_maker", {})
        dm_name = dm.get("full_name") or "Executive"
        dm_title = dm.get("title") or "Leadership"
        bottleneck = account.get("process_bottleneck_hypothesis", "Cross-system synchronization drag")
        trigger = account.get("operational_pain_trigger", "Scaling operations")
        
        mermaid_code = self.generator._build_mermaid_diagram(account)
        encoded_mermaid = base64.urlsafe_b64encode(mermaid_code.encode("utf-8")).decode("utf-8")
        diagram_image_url = f"https://mermaid.ink/img/{encoded_mermaid}"
        email_reply = account.get("architecture_blueprint", {}).get("email_reply_template") or self.generator.generate_email_reply(account)

        blocks = [
            # 1. Header Callout (Executive Context)
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"type": "emoji", "emoji": "💡"},
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"Executive Benchmark Context (20–80 Employee Scale):\n"
                                           f"• Target Executive: {dm_name} ({dm_title}) • Domain: {domain}\n"
                                           f"• Observed Friction: {bottleneck}\n"
                                           f"• Operational Trigger: {trigger}\n"
                                           f"• Delivery Standard: Google Cloud Solution Architecture (100% Async / Zero Calls)"
                            }
                        }
                    ]
                }
            },
            {"object": "block", "type": "divider", "divider": {}},

            # 2. Section 1: Architecture Blueprint (Image only, zero code displayed)
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "1. 🏗️ Target System Architecture"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Event-driven, self-healing pipeline architecture blueprint:"}
                        }
                    ]
                }
            },
            {
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {
                        "url": diagram_image_url
                    }
                }
            },
            {"object": "block", "type": "divider", "divider": {}},

            # 3. Section 2: Technical Component Breakdown
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "2. ⚙️ Technical Component Breakdown"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "1. Ingestion & Webhook Layer: Captures webhooks with HMAC signature verification, zero latency, and automatic retry queues."}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "2. Cloud Event Buffer (Idempotent FIFO): Guarantees strict sequential delivery and deduplication, preventing race conditions."}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "3. Async Reconciliation Engine: Stateless worker reconciles business schemas and matches orders/invoices deterministically."}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "4. Destination Sync & Slack Audit: Broadcasts atomic state updates and real-time anomaly alerts to private ops channels."}}]
                }
            },
            {"object": "block", "type": "divider", "divider": {}},

            # 4. Section 3: Projected ROI
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "3. 📊 Projected Business Impact & ROI"}}]
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"type": "emoji", "emoji": "📈"},
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Validated Benchmark ROI for Peer Organizations:\n"
                                           "• Time Saved: 20 to 30 hours per week of manual spreadsheet triage eliminated.\n"
                                           "• OPEX Reduction: 40%–60% reduction in ops coordination overhead.\n"
                                           "• Error Rate: Reduced to < 0.05% via deterministic schema validation.\n"
                                           "• Turnaround SLA: Process cycle reduced from 24–48 hours to < 3 seconds real-time."
                            }
                        }
                    ]
                }
            },
            {"object": "block", "type": "divider", "divider": {}},

            # 5. Section 4: 2-Week Async Roadmap
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "4. 🚀 2-Week Async Implementation Roadmap"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Phase 1 (Days 1–3): Calibration & Schema Mapping — API token handshake, schema validation in Notion. (Client time: < 30 mins text review)"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Phase 2 (Days 4–8): Event Pipeline & Shadow Dry-Run — Deploy serverless workers, run parallel shadow reconciliation. (Client time: 0 mins)"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Phase 3 (Days 9–14): Production Cutover & Slack Audit — Live routing cutover, automated Slack audit trail activated. (Client time: 15 mins signoff)"}}]
                }
            },
            {"object": "block", "type": "divider", "divider": {}},

            # 6. Section 5: Ready-to-Send Email Reply
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "5. ✉️ Ready-to-Send Email Reply (US Business English)"}}]
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"type": "emoji", "emoji": "✉️"},
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"Copy and send this when {dm_name} replies 'Yes, send it over':\n\n{email_reply}"}
                        }
                    ]
                }
            },
            {"object": "block", "type": "divider", "divider": {}},

            # 7. Section 6: Security and Custom Adaptation
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "6. 🛡️ Security, Compliance & Custom Adaptation"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "Zero Data Retention (ZDR): Payloads are processed in-flight with end-to-end TLS 1.3 encryption. Customer PII is never permanently stored."}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "SOC2 & GDPR Aligned: Single-tenant cloud function workers with least-privilege IAM roles and SHA-256 Slack audit logging."}}]
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"type": "emoji", "emoji": "🛠️"},
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"Tailored Customization Promise for {name}:\n"
                                           f"This blueprint represents our proven benchmark pattern. If your internal tech stack or edge cases differ, "
                                           f"we adapt this architecture specifically to your exact business workflows in 48 hours—100% asynchronously with zero meetings."
                            }
                        }
                    ]
                }
            }
        ]

        return blocks

    def publish_account_to_notion(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """
        Публікує архітектурне рішення конкретного акаунту у Notion під батьківську сторінку.
        Повертає URL новоствореної сторінки Notion.
        """
        if not self.token or not self.parent_page_id:
            return {"success": False, "error": "NOTION_TOKEN або NOTION_PARENT_PAGE_ID не вказано."}

        name = account.get("name", "Company")
        domain = account.get("domain", "")
        acc_id = account.get("id", f"acc-{domain.replace('.', '-')}")

        # Якщо сторінка вже існувала раніше, архівуємо стару, щоб уникнути дублікатів
        old_page_id = account.get("architecture_blueprint", {}).get("notion_page_id")
        if old_page_id:
            try:
                requests.patch(
                    f"{self.base_url}/pages/{old_page_id}",
                    headers=self._get_headers(),
                    json={"archived": True},
                    timeout=10
                )
            except Exception as e:
                print(f"  ℹ️ Не вдалося заархівувати попередню сторінку {old_page_id}: {e}")

        blocks = self.build_notion_blocks(account)

        payload = {
            "parent": {"page_id": self.parent_page_id},
            "icon": {"type": "emoji", "emoji": "📐"},
            "properties": {
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": f"📐 Architecture Blueprint: {name} ({domain})"}
                        }
                    ]
                }
            },
            "children": blocks
        }

        try:
            res = requests.post(
                f"{self.base_url}/pages",
                headers=self._get_headers(),
                json=payload,
                timeout=25
            )

            if res.status_code == 200:
                p_data = res.json()
                page_url = p_data.get("url")
                page_id = p_data.get("id")
                return {
                    "success": True,
                    "notion_url": page_url,
                    "notion_page_id": page_id,
                    "name": name,
                    "domain": domain
                }
            else:
                return {
                    "success": False,
                    "status_code": res.status_code,
                    "error": res.text,
                    "name": name
                }
        except Exception as e:
            return {"success": False, "error": str(e), "name": name}

    def sync_all_accounts(self, kb_path: str = "data/memory/knowledge_base.json", verified_path: str = "data/verified_consulting_leads.json") -> Dict[str, Any]:
        """
        Синхронізує всі 10 акаунтів з Notion і зберігає посилання в базах даних.
        """
        if not os.path.exists(kb_path):
            return {"success": False, "error": f"{kb_path} not found"}

        with open(kb_path, "r", encoding="utf-8") as f:
            kb_data = json.load(f)

        accounts = kb_data.get("accounts", [])
        synced_results = []
        errors = []

        print(f"🚀 Запуск синхронізації {len(accounts)} акаунтів у Notion...")
        for i, acc in enumerate(accounts, 1):
            name = acc.get("name", "Unknown")
            print(f"[{i}/{len(accounts)}] Публікація блюпринту для {name}...")
            res = self.publish_account_to_notion(acc)

            if res.get("success"):
                n_url = res.get("notion_url")
                n_id = res.get("notion_page_id")
                acc.setdefault("architecture_blueprint", {})
                acc["architecture_blueprint"]["notion_url"] = n_url
                acc["architecture_blueprint"]["notion_page_id"] = n_id
                acc["architecture_blueprint"]["notion_synced_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                synced_results.append({"name": name, "url": n_url})
                print(f"  ✅ Успішно! Notion URL: {n_url}")
            else:
                errors.append({"name": name, "error": res.get("error")})
                print(f"  ❌ Помилка для {name}: {res.get('error')}")

            # Дотримання Rate Limit Notion API (3 req/sec)
            time.sleep(0.4)

        # Збереження оновленої Knowledge Base
        with open(kb_path, "w", encoding="utf-8") as f:
            json.dump(kb_data, f, indent=2, ensure_ascii=False)

        # Також оновлюємо verified_consulting_leads.json
        if os.path.exists(verified_path):
            with open(verified_path, "r", encoding="utf-8") as f:
                v_data = json.load(f)
            url_map = {r["name"]: r["url"] for r in synced_results}
            for lead in v_data.get("leads", []):
                l_name = lead.get("name")
                if l_name in url_map:
                    lead.setdefault("architecture_blueprint", {})
                    lead["architecture_blueprint"]["notion_url"] = url_map[l_name]
            with open(verified_path, "w", encoding="utf-8") as f:
                json.dump(v_data, f, indent=2, ensure_ascii=False)

        return {
            "success": len(synced_results) > 0,
            "total_synced": len(synced_results),
            "total_failed": len(errors),
            "synced_pages": synced_results,
            "errors": errors
        }

if __name__ == "__main__":
    publisher = NotionPublisher()
    test_res = publisher.test_connection()
    print("Test connection:", test_res)
    if test_res.get("success"):
        res = publisher.sync_all_accounts()
        print("Sync results:", res)
