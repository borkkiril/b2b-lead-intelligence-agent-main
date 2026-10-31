"""
AI Prospecting Agent (Orion) — B2B Lead Intelligence Dashboard
Чистий візуальний інтерфейс бази даних лідів (ЄС, UK, Україна).
Працює 100% автономно з локальною SQLite базою даних (data/leads.db) та knowledge_base.json без платних зовнішніх API.
Підтримує 11 обов'язкових полів:
inbox_slot, company, country, website, industry_problem_x, contact_role,
verified_email, mx_status, email_step1_plain_text, notion_adaptation_blueprint, status.
"""

import sys
import threading
import flet as ft

from core.database import (
    init_db,
    get_leads,
    update_lead_status,
    count_metrics,
    export_to_json,
    sync_from_json
)
from ui.header import DashboardHeader
from ui.sidebar import DashboardSidebar
from ui.modals import (
    launch_system_browser,
    copy_to_clipboard,
    create_email_preview_dialog,
    create_blueprint_preview_dialog,
    create_account_details_dialog
)
from ui.theme import (
    FONT_DIALOG_TITLE,
    FONT_BODY,
    FONT_CAPTION,
    FONT_TAG,
    BG_PAGE,
    BG_SURFACE,
    BORDER_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    COLOR_PRIMARY,
    COLOR_PRIMARY_LIGHT,
    COLOR_SUCCESS,
    COLOR_SUCCESS_LIGHT,
    COLOR_WARNING,
    COLOR_WARNING_LIGHT,
    COLOR_INDIGO,
    COLOR_INDIGO_LIGHT
)

# Mutex lock guarding background JSON synchronization against race conditions
json_export_lock = threading.Lock()

def _safe_export_to_json():
    with json_export_lock:
        export_to_json()

def main(page: ft.Page):
    page.title = "B2B Lead Intelligence Dashboard — AsyncFlow Systems"
    if hasattr(page, "window") and page.window:
        page.window.width = 1440
        page.window.height = 920
        page.window.min_width = 800
        page.window.min_height = 550
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = BG_PAGE
    page.padding = 0

    # 1. Завантаження даних з SQLite (зі синхронізацією з knowledge_base.json)
    init_db()
    sync_from_json()
    accounts = get_leads()

    # Поточні значення фільтрів
    current_search = ""
    current_status = "Всі"
    current_country = "Всі"
    current_inbox = "Всі"

    def handle_update_status(account: dict, outreach_status: str):
        lead_id = account.get("id")
        if lead_id:
            update_lead_status(lead_id, outreach_status)
        account["status"] = outreach_status
        account["outreach_status"] = outreach_status
        
        # Асинхронний експорт у JSON із блокуванням потоку
        threading.Thread(target=_safe_export_to_json, daemon=True).start()
        
        header.update_metrics(get_leads())
        render_table()
        try:
            page.update()
        except Exception:
            pass

    def handle_refresh():
        nonlocal accounts
        accounts = get_leads()
        header.update_metrics(accounts)
        render_table()
        try:
            page.show_dialog(ft.SnackBar(
                content=ft.Text(f"Базу оновлено! Завантажено {len(accounts)} компаній.", color=ft.Colors.WHITE),
                bgcolor=COLOR_PRIMARY,
                duration=2000
            ))
            page.update()
        except Exception:
            pass

    def handle_filter_change(query: str, status: str, country: str, inbox: str):
        nonlocal current_search, current_status, current_country, current_inbox
        current_search = (query or "").strip()
        current_status = status
        current_country = country
        current_inbox = inbox
        render_table()
        try:
            page.update()
        except Exception:
            pass

    # 2. Фільтрація списку лідів через оптимізовані індекси SQLite
    def get_filtered_accounts():
        return get_leads(
            status=current_status,
            country=current_country,
            inbox_slot=current_inbox,
            search=current_search
        )

    # 3. Контейнер таблиці
    table_container = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=12)

    def render_table():
        items = get_filtered_accounts()
        table_container.controls.clear()

        if not items:
            table_container.controls.append(
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding.all(50),
                    content=ft.Column([
                        ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=50, color=TEXT_MUTED),
                        ft.Text("Не знайдено жодної компанії за обраними фільтрами", size=FONT_DIALOG_TITLE, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY),
                        ft.Text(
                            "Спробуйте змінити фільтри або додайте нові контакти через скіл instant-closer.",
                            size=FONT_BODY,
                            color=TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
                )
            )
            return

        for i, acc in enumerate(items, 1):
            table_container.controls.append(create_lead_card(acc, i))

    def create_lead_card(acc: dict, index: int):
        company = acc.get("company") or acc.get("name", "Компанія")
        website = acc.get("website") or acc.get("domain", "")
        country = acc.get("country") or acc.get("headquarters", "ЄС")
        inbox_slot = acc.get("inbox_slot", "Пошта 1")
        problem = acc.get("industry_problem_x") or acc.get("operational_pain_trigger", "—")
        contact_role = acc.get("contact_role") or "Decision Maker"
        email = acc.get("verified_email") or acc.get("decision_maker", {}).get("primary_email", "—")
        mx_status = acc.get("mx_status") or "Verified MX Live"
        status = acc.get("status") or acc.get("outreach_status") or "Не відправлено"

        # Verification badge
        verif_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=14, color=COLOR_SUCCESS),
                ft.Text(mx_status, size=FONT_TAG, weight=ft.FontWeight.W_600, color=COLOR_SUCCESS)
            ], spacing=4),
            bgcolor=COLOR_SUCCESS_LIGHT,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=6
        )

        # Country badge
        country_badge = ft.Container(
            content=ft.Text(country, size=FONT_TAG, weight=ft.FontWeight.W_600, color=COLOR_INDIGO),
            bgcolor=COLOR_INDIGO_LIGHT,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=6
        )

        # Inbox slot badge
        inbox_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.EMAIL_OUTLINED, size=13, color=COLOR_PRIMARY),
                ft.Text(inbox_slot, size=FONT_TAG, weight=ft.FontWeight.BOLD, color=COLOR_PRIMARY)
            ], spacing=3),
            bgcolor=COLOR_PRIMARY_LIGHT,
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=6
        )

        def on_status_change(e):
            handle_update_status(acc, e.control.value)

        status_select = ft.Dropdown(
            value=status,
            options=[
                ft.dropdown.Option("Не відправлено"),
                ft.dropdown.Option("Відправлено"),
                ft.dropdown.Option("Отримано відповідь"),
            ],
            dense=True,
            width=180,
            text_size=FONT_CAPTION,
            on_select=on_status_change
        )

        card = ft.Container(
            bgcolor=BG_SURFACE,
            border=ft.Border.all(1, BORDER_COLOR),
            border_radius=10,
            padding=14,
            content=ft.Column([
                # Row 1: Header info and actions
                ft.Row([
                    ft.Text(f"#{index}", size=FONT_BODY, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                    ft.Text(company, size=FONT_DIALOG_TITLE, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    inbox_badge,
                    country_badge,
                    verif_badge,
                    ft.Container(expand=True),
                    ft.TextButton(
                        f"🌐 {website}",
                        on_click=lambda e: launch_system_browser(f"https://{website}" if not website.startswith("http") else website)
                    ) if website else ft.Container(),
                    ft.FilledButton(
                        "✉️ Лист №1 (Plain)",
                        icon=ft.Icons.EMAIL_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY_LIGHT, color=COLOR_PRIMARY),
                        on_click=lambda e: create_email_preview_dialog(page, acc, handle_update_status)
                    ),
                    ft.FilledButton(
                        "📄 Notion Блюпринт",
                        icon=ft.Icons.DESCRIPTION_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=COLOR_INDIGO_LIGHT, color=COLOR_INDIGO),
                        on_click=lambda e: create_blueprint_preview_dialog(page, acc)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.INFO_OUTLINE_ROUNDED,
                        tooltip="Повне досьє",
                        icon_color=COLOR_PRIMARY,
                        icon_size=20,
                        on_click=lambda e: create_account_details_dialog(page, acc, handle_update_status)
                    )
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),

                ft.Divider(height=10, color=BORDER_COLOR),

                # Row 2: Problem X + Contact + Email + Status Selector
                ft.Row([
                    # Problem X
                    ft.Container(
                        expand=5,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.BOLT_ROUNDED, size=15, color=COLOR_WARNING),
                                ft.Text("Галузева проблема Х (Операційне вузьке місце):", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=TEXT_MUTED)
                            ], spacing=4),
                            ft.Text(problem, size=FONT_BODY, color=TEXT_PRIMARY, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS)
                        ], spacing=2)
                    ),

                    ft.VerticalDivider(width=16, color=BORDER_COLOR),

                    # Contact & Role
                    ft.Container(
                        expand=3,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.PERSON_OUTLINE_ROUNDED, size=15, color=COLOR_INDIGO),
                                ft.Text("ОПР та Роль:", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                            ], spacing=4),
                            ft.Text(contact_role, size=FONT_BODY, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        ], spacing=2)
                    ),

                    ft.VerticalDivider(width=16, color=BORDER_COLOR),

                    # Verified Email
                    ft.Container(
                        expand=3,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.ALTERNATE_EMAIL_ROUNDED, size=15, color=COLOR_PRIMARY),
                                ft.Text("Робочий Email:", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                                ft.IconButton(
                                    icon=ft.Icons.CONTENT_COPY_ROUNDED,
                                    tooltip="Скопіювати email",
                                    icon_size=15,
                                    icon_color=COLOR_PRIMARY,
                                    on_click=lambda e: copy_to_clipboard(page, email, "Email скопійовано!")
                                ) if email and email != "—" else ft.Container()
                            ], spacing=4),
                            ft.Text(email, size=FONT_BODY, weight=ft.FontWeight.W_500, color=COLOR_PRIMARY if email != "—" else TEXT_MUTED)
                        ], spacing=2)
                    ),

                    ft.VerticalDivider(width=16, color=BORDER_COLOR),

                    # Status Dropdown
                    ft.Container(
                        expand=2,
                        content=ft.Column([
                            ft.Text("Статус аутрічу:", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                            status_select
                        ], spacing=3)
                    )
                ], vertical_alignment=ft.CrossAxisAlignment.START)
            ], spacing=6)
        )
        return card

    # 4. Монтування дашборду
    header = DashboardHeader(accounts=accounts, on_refresh=handle_refresh)
    sidebar = DashboardSidebar(on_filter_change=handle_filter_change)

    render_table()

    main_layout = ft.Column([
        header,
        ft.Row([
            sidebar,
            ft.Container(
                content=table_container,
                expand=True,
                padding=16,
                bgcolor=BG_PAGE
            )
        ], expand=True, spacing=0)
    ], expand=True, spacing=0)

    page.add(main_layout)

if __name__ == "__main__":
    if "--web" in sys.argv or "-w" in sys.argv:
        print("🌐 Запуск веб-інтерфейсу B2B Lead Dashboard на http://localhost:8550...")
        try:
            ft.run(main, host="0.0.0.0", port=8550, view=ft.AppView.WEB_BROWSER)
        except Exception as e:
            print(f"Попередження відкриття браузера: {e}. Запуск у режимі сервера...")
            ft.run(main, host="0.0.0.0", port=8550, view=None)
    else:
        try:
            ft.run(main)
        except Exception as e:
            print(f"Десктопний запуск: {e}. Перехід на веб-інтерфейс (http://localhost:8550)...")
            try:
                ft.run(main, host="0.0.0.0", port=8550, view=ft.AppView.WEB_BROWSER)
            except Exception:
                ft.run(main, host="0.0.0.0", port=8550, view=None)
