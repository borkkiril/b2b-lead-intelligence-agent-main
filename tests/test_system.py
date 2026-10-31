"""
Automated Test Suite for B2B Lead Intelligence Dashboard.
Covers:
1. SQLite Database creation & schema integrity (all 11 fields).
2. Full CRUD Lifecycle (INSERT, SELECT, UPDATE status, DELETE) on isolated test lead.
3. Smoke Test for Visual UI (imports, component compilation, page mount, modal generation).
"""

import os
import sys
import unittest
import py_compile
from unittest.mock import MagicMock

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database import (
    init_db,
    verify_table_integrity,
    insert_lead,
    get_leads,
    get_lead_by_id,
    update_lead_status,
    update_unsent_lead,
    delete_lead,
    count_metrics,
    get_connection,
    LeadRecord
)

class TestDatabaseIntegrityAndCRUD(unittest.TestCase):
    def setUp(self):
        self.test_db = os.path.join(PROJECT_ROOT, "data", "test_leads.db")
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        init_db(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_01_schema_integrity(self):
        """Verify database table creation and schema integrity (all 11 required fields)."""
        self.assertTrue(verify_table_integrity(self.test_db), "Table schema does not contain all required columns!")
        
        with get_connection(self.test_db) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(leads);")
            columns = {row["name"]: row["type"] for row in cursor.fetchall()}
            
        required_cols = [
            "id", "inbox_slot", "company", "country", "website",
            "industry_problem_x", "contact_role", "verified_email",
            "mx_status", "email_step1_plain_text", "email_step1_5_followup",
            "notion_adaptation_blueprint", "status", "created_at"
        ]
        for col in required_cols:
            self.assertIn(col, columns, f"Column {col} not found in leads table.")

    def test_02_crud_lifecycle(self):
        """Full CRUD lifecycle: INSERT -> SELECT -> UPDATE -> DELETE on test lead."""
        test_payload = {
            "inbox_slot": "Inbox 1",
            "company": "Automated Test Logistics GmbH",
            "country": "🇩🇪 Germany (Berlin)",
            "website": "test-logistics.de",
            "industry_problem_x": "Manual invoice audit and warehouse ERP desynchronization.",
            "contact_role": "Maximilian Weber (Chief Operating Officer)",
            "verified_email": "m.weber@test-logistics.de",
            "mx_status": "Verified MX (Outlook) + HTTP 200 Live",
            "email_step1_plain_text": "Hi Maximilian, quick question on your warehouse reconciliation workflows...",
            "email_step1_5_followup": "Hi Maximilian, just following up — our modular Staging Sandbox architecture validates workflow changes in complete isolation (0% risk of breaking production ERP), backed by a contractual guarantee to identify at least $20,000 in annual operational waste. Happy to answer any questions you may have.",
            "notion_adaptation_blueprint": "### 1. Logistics Bottleneck Blueprint\n5-Day Zero-Meeting Audit.",
            "status": "Draft"
        }

        # 1. INSERT
        lead_id = insert_lead(test_payload, self.test_db)
        self.assertIsNotNone(lead_id)
        self.assertGreater(lead_id, 0, "INSERT did not return valid id.")

        # 2. SELECT
        lead = get_lead_by_id(lead_id, self.test_db)
        self.assertIsNotNone(lead, "SELECT did not find newly inserted record.")
        self.assertEqual(lead["company"], "Automated Test Logistics GmbH")
        self.assertEqual(lead["inbox_slot"], "Inbox 1")
        self.assertEqual(lead["verified_email"], "m.weber@test-logistics.de")
        self.assertEqual(lead["status"], "Draft")

        # 3. UPDATE status
        updated = update_lead_status(lead_id, "Sent", self.test_db)
        self.assertTrue(updated, "UPDATE failed to update status.")
        lead_after_update = get_lead_by_id(lead_id, self.test_db)
        self.assertEqual(lead_after_update["status"], "Sent", "Status after UPDATE does not match.")

        # 4. DELETE
        deleted = delete_lead(lead_id, self.test_db)
        self.assertTrue(deleted, "DELETE did not remove test record.")
        lead_after_delete = get_lead_by_id(lead_id, self.test_db)
        self.assertIsNone(lead_after_delete, "Test record still exists after DELETE!")

    def test_03_pydantic_validation_and_unsent_guard(self):
        """Pydantic v2 validation and unsent draft modification guard (update_unsent_lead)."""
        # 1. Create with LeadRecord
        record_obj = LeadRecord(
            inbox_slot="Inbox 2",
            company="Pydantic Validated Corp",
            country="🇬🇧 UK (London)",
            website="https://pydantic-corp.co.uk",
            industry_problem_x="Data inconsistency",
            contact_role="Director of Ops",
            verified_email="ops@pydantic-corp.co.uk",
            status="Draft"
        )
        lead_id = insert_lead(record_obj, self.test_db)
        self.assertIsNotNone(lead_id)

        # 2. Updating unsent draft should succeed
        ok = update_unsent_lead(lead_id, {"email_step1_plain_text": "Updated draft copy"}, self.test_db)
        self.assertTrue(ok, "update_unsent_lead should allow updating record with status 'Draft'.")
        lead = get_lead_by_id(lead_id, self.test_db)
        self.assertEqual(lead["email_step1_plain_text"], "Updated draft copy")

        # 3. Mark lead as 'Sent'
        update_lead_status(lead_id, "Sent", self.test_db)

        # 4. Attempt to update sent lead must be blocked at SQL level
        blocked = update_unsent_lead(lead_id, {"email_step1_plain_text": "Illegal overwrite attempt"}, self.test_db)
        self.assertFalse(blocked, "update_unsent_lead MUST NOT permit updating sent leads!")
        lead_after = get_lead_by_id(lead_id, self.test_db)
        self.assertEqual(lead_after["email_step1_plain_text"], "Updated draft copy", "Sent content was overwritten!")

class TestAppUIAndSmoke(unittest.TestCase):
    def test_01_syntax_and_imports(self):
        """Verify Python file syntax and imports without errors."""
        files = [
            "main.py",
            "core/database.py",
            "core/cache_manager.py",
            "core/rodo_compliance.py",
            "ui/header.py",
            "ui/sidebar.py",
            "ui/modals.py",
            "ui/theme.py"
        ]
        for f in files:
            path = os.path.join(PROJECT_ROOT, f)
            try:
                py_compile.compile(path, doraise=True)
            except Exception as e:
                self.fail(f"Compilation error in file {f}: {e}")

    def test_02_ui_mount_and_modals(self):
        """Smoke test for Flet UI rendering and modal dialog instantiation."""
        import flet as ft
        from main import main
        from ui.header import DashboardHeader
        from ui.sidebar import DashboardSidebar
        from ui.modals import (
            create_email_preview_dialog,
            create_blueprint_preview_dialog,
            create_account_details_dialog
        )

        class MockPage:
            def __init__(self):
                self.title = ""
                self.theme_mode = None
                self.bgcolor = None
                self.padding = None
                self.window = MagicMock()
                self.controls = []
            def add(self, *c):
                self.controls.extend(c)
            def update(self):
                pass
            def show_dialog(self, dlg):
                pass

        mock_page = MockPage()

        # Test mounting main(page)
        try:
            main(mock_page)
        except Exception as e:
            self.fail(f"Error during main(page) execution: {e}")

        self.assertGreater(len(mock_page.controls), 0, "main(page) did not mount controls to page.")

        # Dialog generation test
        sample_lead = {
            "id": 9999,
            "inbox_slot": "Inbox 1",
            "company": "Smoke Test Corp",
            "country": "EU",
            "website": "smoketest.eu",
            "industry_problem_x": "Desync issue",
            "contact_role": "CEO (Test)",
            "verified_email": "ceo@smoketest.eu",
            "mx_status": "Verified MX Live",
            "email_step1_plain_text": "Plain text email",
            "notion_adaptation_blueprint": "Blueprint text",
            "status": "Draft"
        }

        dlg1 = create_email_preview_dialog(mock_page, sample_lead, lambda a, s: None)
        self.assertIsInstance(dlg1, ft.AlertDialog, "create_email_preview_dialog did not return AlertDialog.")

        dlg2 = create_blueprint_preview_dialog(mock_page, sample_lead)
        self.assertIsInstance(dlg2, ft.AlertDialog, "create_blueprint_preview_dialog did not return AlertDialog.")

        dlg3 = create_account_details_dialog(mock_page, sample_lead, lambda a, s: None)
        self.assertIsInstance(dlg3, ft.AlertDialog, "create_account_details_dialog did not return AlertDialog.")


class TestRODOComplianceGuard(unittest.TestCase):
    def test_01_redact_personal_phone_and_pesel(self):
        """Verify masking of personal phones, PESEL numbers, and national IDs (RODO/GDPR)."""
        from core.rodo_compliance import RODOComplianceGuard

        sample_input = (
            "Kandydat Jan Kowalski, PESEL: 85031212345, Dowód: ABC 123456. "
            "Kontakt telefoniczny: +48 601 234 567 lub 502987654."
        )
        redacted = RODOComplianceGuard.redact_pii_before_llm(sample_input)

        self.assertNotIn("85031212345", redacted, "PESEL was not redacted!")
        self.assertNotIn("ABC 123456", redacted, "National ID was not redacted!")
        self.assertNotIn("601 234 567", redacted, "Phone was not redacted!")
        self.assertNotIn("502987654", redacted, "Phone without prefix was not redacted!")
        self.assertIn("[REDACTED_PESEL_OR_ID]", redacted)
        self.assertIn("[REDACTED_PHONE]", redacted)

    def test_02_redact_private_email_keep_corporate(self):
        """Verify redaction of private mailboxes (@gmail, @wp.pl) while preserving corporate B2B."""
        from core.rodo_compliance import RODOComplianceGuard

        text = (
            "Przesyłam list do: kontakt prywatny janek@wp.pl oraz kowalski@gmail.com. "
            "Do wiadomości zarząd: p.nowak@enterprise-logistics.pl oraz tech@b2b-analytics.io."
        )
        redacted = RODOComplianceGuard.redact_pii_before_llm(text)

        self.assertNotIn("janek@wp.pl", redacted, "Private email wp.pl was not redacted!")
        self.assertNotIn("kowalski@gmail.com", redacted, "Private email gmail.com was not redacted!")
        self.assertIn("[REDACTED_PRIVATE_EMAIL]", redacted)

        # Corporate B2B addresses must be preserved under Art. 6(1)(f) GDPR
        self.assertIn("p.nowak@enterprise-logistics.pl", redacted, "Corporate B2B email was mistakenly removed!")
        self.assertIn("tech@b2b-analytics.io", redacted, "Corporate B2B email was mistakenly removed!")

    def test_03_validate_b2b_record_compliance(self):
        """Verify RODO compliance audit for B2B records (corporate domain vs consumer webmail)."""
        from core.rodo_compliance import RODOComplianceGuard

        # 1. Valid B2B contact
        valid_res = RODOComplianceGuard.validate_b2b_record_compliance("alex@enterprise-logistics.pl", "enterprise-logistics.pl")
        self.assertTrue(valid_res["is_compliant"])
        self.assertEqual(valid_res["risk_level"], "LOW")
        self.assertIn("Legitimate Business Interest", valid_res["legal_basis"])

        # 2. Invalid consumer contact (Onet webmail)
        invalid_res = RODOComplianceGuard.validate_b2b_record_compliance("adam@onet.pl", "onet.pl")
        self.assertFalse(invalid_res["is_compliant"])
        self.assertEqual(invalid_res["risk_level"], "HIGH")
        self.assertIn("CONSUMER_MAILBOX_DETECTED", invalid_res["flags"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
