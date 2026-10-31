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
        """Перевірка створення та цілісності схеми БД (наявність усіх 11 обов'язкових полів)."""
        self.assertTrue(verify_table_integrity(self.test_db), "Схема таблиці leads не містить усіх 11 обов'язкових колонок!")
        
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
            self.assertIn(col, columns, f"Колонку {col} не знайдено в таблиці leads.")

    def test_02_crud_lifecycle(self):
        """Повний цикл CRUD: INSERT -> SELECT -> UPDATE -> DELETE тестового ліда."""
        test_payload = {
            "inbox_slot": "Пошта 1",
            "company": "Automated Test Logistics GmbH",
            "country": "🇩🇪 Німеччина (Berlin)",
            "website": "test-logistics.de",
            "industry_problem_x": "Ручна звірка накладних та розсинхрон зі складською ERP системою.",
            "contact_role": "Maximilian Weber (Chief Operating Officer)",
            "verified_email": "m.weber@test-logistics.de",
            "mx_status": "Verified MX (Outlook) + HTTP 200 Live",
            "email_step1_plain_text": "Hi Maximilian, quick question on your warehouse reconciliation workflows...",
            "email_step1_5_followup": "Hi Maximilian, just following up — our modular Staging Sandbox architecture validates workflow changes in complete isolation (0% risk of breaking production ERP), backed by a contractual guarantee to identify at least $20,000 in annual operational waste. Happy to answer any questions you may have.",
            "notion_adaptation_blueprint": "### 1. Logistics Bottleneck Blueprint\n5-Day Zero-Meeting Audit.",
            "status": "Не відправлено"
        }

        # 1. INSERT
        lead_id = insert_lead(test_payload, self.test_db)
        self.assertIsNotNone(lead_id)
        self.assertGreater(lead_id, 0, "INSERT не повернув валідний id.")

        # 2. SELECT
        lead = get_lead_by_id(lead_id, self.test_db)
        self.assertIsNotNone(lead, "SELECT не знайшов щойно доданий запис.")
        self.assertEqual(lead["company"], "Automated Test Logistics GmbH")
        self.assertEqual(lead["inbox_slot"], "Пошта 1")
        self.assertEqual(lead["verified_email"], "m.weber@test-logistics.de")
        self.assertEqual(lead["status"], "Не відправлено")

        # 3. UPDATE status
        updated = update_lead_status(lead_id, "Відправлено", self.test_db)
        self.assertTrue(updated, "UPDATE не зміг оновити статус.")
        lead_after_update = get_lead_by_id(lead_id, self.test_db)
        self.assertEqual(lead_after_update["status"], "Відправлено", "Статус після UPDATE не збігається.")

        # 4. DELETE
        deleted = delete_lead(lead_id, self.test_db)
        self.assertTrue(deleted, "DELETE не видалив тестовий запис.")
        lead_after_delete = get_lead_by_id(lead_id, self.test_db)
        self.assertIsNone(lead_after_delete, "Тестовий запис все ще існує після DELETE!")

    def test_03_pydantic_validation_and_unsent_guard(self):
        """Перевірка валідації Pydantic v2 та захисту від модифікації відправлених лідів (update_unsent_lead)."""
        # 1. Створення через LeadRecord
        record_obj = LeadRecord(
            inbox_slot="Пошта 2",
            company="Pydantic Validated Corp",
            country="🇬🇧 UK (London)",
            website="https://pydantic-corp.co.uk",
            industry_problem_x="Data inconsistency",
            contact_role="Director of Ops",
            verified_email="ops@pydantic-corp.co.uk",
            status="Не відправлено"
        )
        lead_id = insert_lead(record_obj, self.test_db)
        self.assertIsNotNone(lead_id)

        # 2. Оновлення невідправленої чернетки має пройти успішно
        ok = update_unsent_lead(lead_id, {"email_step1_plain_text": "Updated draft copy"}, self.test_db)
        self.assertTrue(ok, "update_unsent_lead має оновлювати запис зі статусом 'Не відправлено'.")
        lead = get_lead_by_id(lead_id, self.test_db)
        self.assertEqual(lead["email_step1_plain_text"], "Updated draft copy")

        # 3. Переводимо лід у статус 'Відправлено'
        update_lead_status(lead_id, "Відправлено", self.test_db)

        # 4. Спроба оновити вже відправлений лід повинна бути заблокована на рівні SQL
        blocked = update_unsent_lead(lead_id, {"email_step1_plain_text": "Illegal overwrite attempt"}, self.test_db)
        self.assertFalse(blocked, "update_unsent_lead НЕ повинен дозволяти оновлення для відправлених листів!")
        lead_after = get_lead_by_id(lead_id, self.test_db)
        self.assertEqual(lead_after["email_step1_plain_text"], "Updated draft copy", "Відправлений контент було перезаписано!")

class TestAppUIAndSmoke(unittest.TestCase):
    def test_01_syntax_and_imports(self):
        """Перевірка синтаксису Python-файлів та імпортів без помилок."""
        files = [
            "main.py",
            "core/database.py",
            "core/cache_manager.py",
            "core/rodo_compliance.py",
            "core/health_monitor.py",
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
                self.fail(f"Помилка компіляції файлу {f}: {e}")

    def test_02_ui_mount_and_modals(self):
        """Smoke-тест рендеру інтерфейсу Flet та відкриття модальних вікон."""
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

        # Тест монтування main(page)
        try:
            main(mock_page)
        except Exception as e:
            self.fail(f"Помилка при виконанні main(page): {e}")

        self.assertGreater(len(mock_page.controls), 0, "main(page) не додав жодного кореневого елемента до page.controls.")

        # Тест генерації діалогів
        sample_lead = {
            "id": 9999,
            "inbox_slot": "Пошта 1",
            "company": "Smoke Test Corp",
            "country": "ЄС",
            "website": "smoketest.eu",
            "industry_problem_x": "Desync issue",
            "contact_role": "CEO (Test)",
            "verified_email": "ceo@smoketest.eu",
            "mx_status": "Verified MX Live",
            "email_step1_plain_text": "Plain text email",
            "notion_adaptation_blueprint": "Blueprint text",
            "status": "Не відправлено"
        }

        dlg1 = create_email_preview_dialog(mock_page, sample_lead, lambda a, s: None)
        self.assertIsInstance(dlg1, ft.AlertDialog, "create_email_preview_dialog не повернув AlertDialog.")

        dlg2 = create_blueprint_preview_dialog(mock_page, sample_lead)
        self.assertIsInstance(dlg2, ft.AlertDialog, "create_blueprint_preview_dialog не повернув AlertDialog.")

        dlg3 = create_account_details_dialog(mock_page, sample_lead, lambda a, s: None)
        self.assertIsInstance(dlg3, ft.AlertDialog, "create_account_details_dialog не повернув AlertDialog.")


class TestRODOComplianceGuard(unittest.TestCase):
    def test_01_redact_personal_phone_and_pesel(self):
        """Перевірка маскування номерів телефонів, номерів PESEL та номерів посвідчень (RODO/GDPR)."""
        from core.rodo_compliance import RODOComplianceGuard

        sample_input = (
            "Kandydat Jan Kowalski, PESEL: 85031212345, Dowód: ABC 123456. "
            "Kontakt telefoniczny: +48 601 234 567 lub 502987654."
        )
        redacted = RODOComplianceGuard.redact_pii_before_llm(sample_input)

        self.assertNotIn("85031212345", redacted, "PESEL не був замаскований!")
        self.assertNotIn("ABC 123456", redacted, "Номер посвідчення не був замаскований!")
        self.assertNotIn("601 234 567", redacted, "Телефон не був замаскований!")
        self.assertNotIn("502987654", redacted, "Телефон без префіксу не був замаскований!")
        self.assertIn("[REDACTED_PESEL_OR_ID]", redacted)
        self.assertIn("[REDACTED_PHONE]", redacted)

    def test_02_redact_private_email_keep_corporate(self):
        """Перевірка маскування приватних скриньок (@gmail, @wp.pl) при збереженні корпоративних B2B."""
        from core.rodo_compliance import RODOComplianceGuard

        text = (
            "Przesyłam list do: kontakt prywatny janek@wp.pl oraz kowalski@gmail.com. "
            "Do wiadomości zarząd: p.nowak@enterprise-logistics.pl oraz tech@b2b-analytics.io."
        )
        redacted = RODOComplianceGuard.redact_pii_before_llm(text)

        self.assertNotIn("janek@wp.pl", redacted, "Приватний email wp.pl не був замаскований!")
        self.assertNotIn("kowalski@gmail.com", redacted, "Приватний email gmail.com не був замаскований!")
        self.assertIn("[REDACTED_PRIVATE_EMAIL]", redacted)

        # Корпоративні B2B адреси мають зберігатися для аналізу відповідно до Art. 6(1)(f) GDPR
        self.assertIn("p.nowak@enterprise-logistics.pl", redacted, "Корпоративний B2B email було помилково видалено!")
        self.assertIn("tech@b2b-analytics.io", redacted, "Корпоративний B2B email було помилково видалено!")

    def test_03_validate_b2b_record_compliance(self):
        """Перевірка аудиту RODO для B2B-записів (валідація корпоративного домену проти споживчого)."""
        from core.rodo_compliance import RODOComplianceGuard

        # 1. Валідний B2B контакт
        valid_res = RODOComplianceGuard.validate_b2b_record_compliance("alex@enterprise-logistics.pl", "enterprise-logistics.pl")
        self.assertTrue(valid_res["is_compliant"])
        self.assertEqual(valid_res["risk_level"], "LOW")
        self.assertIn("Legitimate Business Interest", valid_res["legal_basis"])

        # 2. Невалідний приватний контакт (Gmail)
        invalid_res = RODOComplianceGuard.validate_b2b_record_compliance("adam@onet.pl", "onet.pl")
        self.assertFalse(invalid_res["is_compliant"])
        self.assertEqual(invalid_res["risk_level"], "HIGH")
        self.assertIn("CONSUMER_MAILBOX_DETECTED", invalid_res["flags"])


class TestSystemHealthMonitor(unittest.TestCase):
    def test_01_health_check_healthy_database(self):
        """Перевірка телеметрії та працездатності БД (PRAGMA integrity_check, latency)."""
        from core.health_monitor import check_system_health

        test_db = os.path.join(PROJECT_ROOT, "data", "test_health.db")
        if os.path.exists(test_db):
            os.remove(test_db)

        init_db(test_db)
        try:
            report = check_system_health(db_path=test_db, max_latency_ms=100.0)
            self.assertEqual(report["status"], "HEALTHY")
            self.assertEqual(report["db_integrity"], "ok")
            self.assertGreaterEqual(report["db_latency_ms"], 0.0)
            self.assertGreaterEqual(report["quality_sim_score"], 7.0)
            self.assertFalse(report["alert_dispatched"])
        finally:
            if os.path.exists(test_db):
                os.remove(test_db)

    def test_02_health_check_missing_db(self):
        """Перевірка виявлення аварійного стану при відсутності файлу БД."""
        from core.health_monitor import check_system_health

        fake_path = os.path.join(PROJECT_ROOT, "data", "non_existent_404.db")
        report = check_system_health(db_path=fake_path)
        self.assertEqual(report["status"], "CRITICAL")
        self.assertGreater(len(report["issues"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
