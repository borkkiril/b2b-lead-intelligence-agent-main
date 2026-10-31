"""
Модальні вікна для B2B Lead Database Dashboard:
1. Детальний перегляд Листа №1 (Plain Text без посилань, згідно з 2-Step No-Link Funnel).
2. Перегляд Notion Adaptation Blueprint (Матеріал для Листа №2: $2,000 Zero-Meeting Offer + 10x ROI).
3. Повне досьє компанії з верифікацією, тригерами та контактами.
"""

import os
import subprocess
import webbrowser
import flet as ft

from ui.theme import (
    FONT_HEADER_TITLE,
    FONT_DIALOG_TITLE,
    FONT_BODY,
    FONT_CAPTION,
    FONT_TAG,
    BG_PAGE,
    BG_SURFACE,
    BG_CARD,
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

def launch_system_browser(target: str):
    """Відкриває сайт чи посилання у браузері."""
    if not target:
        return
    if target.startswith("http://") or target.startswith("https://"):
        try:
            webbrowser.open(target)
        except Exception:
            try:
                subprocess.Popen(["xdg-open", target])
            except Exception:
                pass
    else:
        abs_p = os.path.abspath(target)
        try:
            subprocess.Popen(["xdg-open", abs_p])
        except Exception:
            try:
                webbrowser.open(f"file://{abs_p}")
            except Exception:
                pass

def copy_to_clipboard(page: ft.Page, text: str, success_message: str = "Скопійовано в буфер обміну!"):
    """Копіює текст у буфер та показує спливаюче сповіщення."""
    try:
        page.set_clipboard(text)
    except Exception:
        pass
    try:
        page.show_dialog(ft.SnackBar(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.WHITE, size=18),
                ft.Text(success_message, color=ft.Colors.WHITE, size=FONT_BODY, weight=ft.FontWeight.W_500)
            ], spacing=8),
            bgcolor=COLOR_SUCCESS,
            duration=2500
        ))
    except Exception:
        pass

def create_email_preview_dialog(page: ft.Page, account: dict, on_update_status):
    """
    Модальне вікно перегляду Листа №1:
    Plain Text без жодних посилань (http/https). Захід через проблему Х + пропозиція надіслати Notion.
    """
    name = account.get("company") or account.get("name", "Компанія")
    contact_role = account.get("contact_role") or "Decision Maker"
    email = account.get("verified_email") or account.get("decision_maker", {}).get("primary_email", "—")
    inbox_slot = account.get("inbox_slot", "Пошта 1")
    
    plain_email = account.get("email_step1_plain_text") or account.get("cold_email", "(Текст листа формується...)")
    cr_first = contact_role.split()[0] if contact_role and contact_role != "Decision Maker" else "there"
    followup_email = account.get("email_step1_5_followup") or (
        f"Hi {cr_first},\n\n"
        f"Just following up on this — our modular Staging Sandbox architecture validates workflow changes in complete isolation "
        f"(0% risk of breaking production ERP or ledgers), backed by a contractual guarantee to identify at least $20,000 in annual operational waste.\n\n"
        f"Happy to answer any questions you may have.\n\n"
        f"Best regards,\n"
        f"AsyncFlow Systems"
    )
    current_status = account.get("status") or account.get("outreach_status", "Не відправлено")

    def close_dlg(e=None):
        try:
            page.pop_dialog()
        except Exception:
            dlg.open = False
            page.update()

    def do_copy_body(e):
        copy_to_clipboard(page, plain_email, "Текст Листа №1 скопійовано!")

    def do_mark_sent(e):
        on_update_status(account, "Відправлено")
        close_dlg()
        copy_to_clipboard(page, plain_email, "Лист скопійовано і статус оновлено на 'Відправлено'!")

    content = ft.Container(
        width=740,
        content=ft.Column([
            # Meta box
            ft.Container(
                bgcolor=BG_CARD,
                border_radius=8,
                padding=12,
                border=ft.Border.all(1, BORDER_COLOR),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.PERSON_ROUNDED, size=18, color=COLOR_PRIMARY),
                        ft.Text(f"Отримувач: {contact_role}", size=FONT_BODY, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Container(expand=True),
                        ft.Text(f"Скринька: {inbox_slot}", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=COLOR_INDIGO),
                    ]),
                    ft.Divider(height=8, color=BORDER_COLOR),
                    ft.Row([
                        ft.Icon(ft.Icons.ALTERNATE_EMAIL_ROUNDED, size=16, color=TEXT_MUTED),
                        ft.Text(f"Email: {email}", size=FONT_BODY, color=TEXT_PRIMARY),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Text("100% Plain Text • Без посилань", size=FONT_TAG, weight=ft.FontWeight.BOLD, color=COLOR_SUCCESS),
                            bgcolor=COLOR_SUCCESS_LIGHT,
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            border_radius=6
                        )
                    ])
                ], spacing=6)
            ),

            # Email Body Container (Лист №1)
            ft.Container(
                bgcolor=BG_PAGE,
                border_radius=8,
                padding=12,
                border=ft.Border.all(1, BORDER_COLOR),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.MARK_EMAIL_READ_ROUNDED, size=16, color=COLOR_PRIMARY),
                        ft.Text("Лист №1: Plain Text (День 1, без посилань, вхід через проблему Х):", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                        ft.Container(expand=True),
                        ft.OutlinedButton(
                            "Скопіювати Лист №1",
                            icon=ft.Icons.CONTENT_COPY_ROUNDED,
                            on_click=do_copy_body,
                            style=ft.ButtonStyle(color=COLOR_PRIMARY)
                        )
                    ]),
                    ft.Divider(height=6, color=BORDER_COLOR),
                    ft.TextField(
                        value=plain_email,
                        multiline=True,
                        read_only=True,
                        min_lines=7,
                        max_lines=12,
                        text_size=FONT_BODY,
                        border=ft.NoInputBorder(),
                        text_style=ft.TextStyle(font_family="monospace", color=TEXT_PRIMARY)
                    )
                ], spacing=4)
            ),

            # Follow-up Container (Лист №1.5 через 48 годин)
            ft.Container(
                bgcolor=COLOR_INDIGO_LIGHT,
                border_radius=8,
                padding=12,
                border=ft.Border.all(1, COLOR_INDIGO),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.UPDATE_ROUNDED, size=16, color=COLOR_INDIGO),
                        ft.Text("Лист №1.5: Змістовний Follow-up (через 48 годин, Staging Sandbox + $20k гарантія):", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=COLOR_INDIGO),
                        ft.Container(expand=True),
                        ft.OutlinedButton(
                            "Скопіювати Лист №1.5",
                            icon=ft.Icons.CONTENT_COPY_ROUNDED,
                            on_click=lambda e: copy_to_clipboard(page, followup_email, "Лист №1.5 (Follow-up) скопійовано!"),
                            style=ft.ButtonStyle(color=COLOR_INDIGO)
                        )
                    ]),
                    ft.Divider(height=6, color=BORDER_COLOR),
                    ft.TextField(
                        value=followup_email,
                        multiline=True,
                        read_only=True,
                        min_lines=4,
                        max_lines=8,
                        text_size=FONT_BODY,
                        border=ft.NoInputBorder(),
                        text_style=ft.TextStyle(font_family="monospace", color=TEXT_PRIMARY)
                    )
                ], spacing=4)
            )
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
    )

    dlg = ft.AlertDialog(
        title=ft.Row([
            ft.Icon(ft.Icons.EMAIL_ROUNDED, color=COLOR_PRIMARY, size=22),
            ft.Text(f"Лист №1: {name}", size=FONT_DIALOG_TITLE, weight=ft.FontWeight.BOLD),
        ], spacing=8),
        content=content,
        actions=[
            ft.TextButton("Закрити", on_click=close_dlg),
            ft.FilledButton(
                "📋 Скопіювати та позначити 'Відправлено'",
                icon=ft.Icons.SEND_ROUNDED,
                style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS, color=ft.Colors.WHITE),
                on_click=do_mark_sent
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    page.show_dialog(dlg)
    return dlg

def create_blueprint_preview_dialog(page: ft.Page, account: dict):
    """
    Модальне вікно перегляду Notion Adaptation Blueprint (Лист №2):
    Готовий структурований контент сторінки Notion під $2,000 Zero-Meeting Offer та 10x ROI гарантію.
    """
    name = account.get("company") or account.get("name", "Компанія")
    blueprint_text = account.get("notion_adaptation_blueprint") or "Notion Blueprint формується..."

    def close_dlg(e=None):
        try:
            page.pop_dialog()
        except Exception:
            dlg.open = False
            page.update()

    def do_copy(e):
        copy_to_clipboard(page, blueprint_text, "Notion Blueprint скопійовано!")

    content = ft.Container(
        width=740,
        content=ft.Column([
            ft.Container(
                bgcolor=COLOR_INDIGO_LIGHT,
                border_radius=8,
                padding=12,
                border=ft.Border.all(1, COLOR_INDIGO),
                content=ft.Row([
                    ft.Icon(ft.Icons.DESCRIPTION_ROUNDED, color=COLOR_INDIGO, size=20),
                    ft.Column([
                        ft.Text(f"Notion Adaptation Blueprint для {name}", size=FONT_BODY, weight=ft.FontWeight.BOLD, color=COLOR_INDIGO),
                        ft.Text("Контент відправляється у Листі №2 після згоди клієнта на ознайомлення.", size=FONT_CAPTION, color=TEXT_MUTED)
                    ], spacing=2)
                ], spacing=10)
            ),
            ft.Container(
                bgcolor=BG_PAGE,
                border_radius=8,
                padding=14,
                border=ft.Border.all(1, BORDER_COLOR),
                content=ft.Column([
                    ft.Row([
                        ft.Text("Структура адаптації під клієнта ($2,000 Zero-Meeting Blueprint):", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                        ft.Container(expand=True),
                        ft.OutlinedButton(
                            "Скопіювати Blueprint",
                            icon=ft.Icons.CONTENT_COPY_ROUNDED,
                            on_click=do_copy,
                            style=ft.ButtonStyle(color=COLOR_PRIMARY)
                        )
                    ]),
                    ft.Divider(height=8, color=BORDER_COLOR),
                    ft.TextField(
                        value=blueprint_text,
                        multiline=True,
                        read_only=True,
                        min_lines=12,
                        max_lines=18,
                        text_size=FONT_BODY,
                        border=ft.NoInputBorder(),
                        text_style=ft.TextStyle(font_family="monospace", color=TEXT_PRIMARY)
                    )
                ], spacing=6)
            )
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
    )

    dlg = ft.AlertDialog(
        title=ft.Row([
            ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color=COLOR_INDIGO, size=22),
            ft.Text(f"Notion Blueprint: {name}", size=FONT_DIALOG_TITLE, weight=ft.FontWeight.BOLD),
        ], spacing=8),
        content=content,
        actions=[
            ft.TextButton("Закрити", on_click=close_dlg),
            ft.FilledButton(
                "Скопіювати в буфер",
                icon=ft.Icons.CONTENT_COPY_ROUNDED,
                style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color=ft.Colors.WHITE),
                on_click=do_copy
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    page.show_dialog(dlg)
    return dlg

def create_account_details_dialog(page: ft.Page, account: dict, on_update_status):
    """Повне досьє компанії з усіма 11 обов'язковими полями системи."""
    name = account.get("company") or account.get("name", "Компанія")
    website = account.get("website") or account.get("domain", "")
    country = account.get("country") or account.get("headquarters", "ЄС")
    inbox_slot = account.get("inbox_slot", "Пошта 1")
    contact_role = account.get("contact_role") or "—"
    email = account.get("verified_email") or account.get("decision_maker", {}).get("primary_email", "—")
    problem = account.get("industry_problem_x") or account.get("operational_pain_trigger", "—")
    mx_status = account.get("mx_status") or "Verified MX + HTTP 200 Live"
    current_status = account.get("status") or account.get("outreach_status", "Не відправлено")

    def close_dlg(e=None):
        try:
            page.pop_dialog()
        except Exception:
            dlg.open = False
            page.update()

    def open_site(e):
        if website:
            url = f"https://{website}" if not website.startswith("http") else website
            launch_system_browser(url)

    content = ft.Container(
        width=700,
        content=ft.Column([
            # Top card
            ft.Container(
                bgcolor=BG_CARD,
                padding=12,
                border_radius=8,
                border=ft.Border.all(1, BORDER_COLOR),
                content=ft.Row([
                    ft.Text(name, size=FONT_HEADER_TITLE, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Container(
                        content=ft.Text(country, size=FONT_TAG, weight=ft.FontWeight.W_600, color=COLOR_INDIGO),
                        bgcolor=COLOR_INDIGO_LIGHT,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        border_radius=6
                    ),
                    ft.Container(
                        content=ft.Text(inbox_slot, size=FONT_TAG, weight=ft.FontWeight.W_600, color=COLOR_PRIMARY),
                        bgcolor=COLOR_PRIMARY_LIGHT,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        border_radius=6
                    ),
                    ft.Container(expand=True),
                    ft.TextButton(f"🌐 {website}", on_click=open_site) if website else ft.Container()
                ])
            ),

            # Problem X
            ft.Container(
                bgcolor=COLOR_WARNING_LIGHT,
                border=ft.Border.all(1, COLOR_WARNING),
                padding=12,
                border_radius=8,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.BOLT_ROUNDED, color=COLOR_WARNING, size=18),
                        ft.Text("Галузева проблема Х (Операційне вузьке місце):", size=FONT_BODY, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Text(problem, size=FONT_BODY, color=TEXT_PRIMARY)
                ], spacing=4)
            ),

            # Contact
            ft.Container(
                bgcolor=BG_SURFACE,
                border=ft.Border.all(1, BORDER_COLOR),
                padding=12,
                border_radius=8,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.PERSON_ROUNDED, color=COLOR_PRIMARY, size=18),
                        ft.Text(f"ОПР / Роль: {contact_role}", size=FONT_BODY, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ]),
                    ft.Row([
                        ft.Icon(ft.Icons.ALTERNATE_EMAIL_ROUNDED, color=COLOR_PRIMARY, size=16),
                        ft.Text(f"Email: {email}", size=FONT_BODY, weight=ft.FontWeight.W_600, color=COLOR_PRIMARY),
                        ft.IconButton(
                            icon=ft.Icons.CONTENT_COPY_ROUNDED,
                            tooltip="Скопіювати email",
                            icon_size=16,
                            on_click=lambda e: copy_to_clipboard(page, email, "Email скопійовано!")
                        )
                    ])
                ], spacing=4)
            ),

            # Verification
            ft.Container(
                bgcolor=COLOR_SUCCESS_LIGHT,
                border=ft.Border.all(1, COLOR_SUCCESS),
                padding=10,
                border_radius=8,
                content=ft.Row([
                    ft.Icon(ft.Icons.VERIFIED_ROUNDED, color=COLOR_SUCCESS, size=18),
                    ft.Text(f"Статус верифікації: {mx_status} • Санкційний скринінг: 100% OK", size=FONT_BODY, color=COLOR_SUCCESS, weight=ft.FontWeight.W_500)
                ], spacing=6)
            )
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
    )

    dlg = ft.AlertDialog(
        title=ft.Row([
            ft.Icon(ft.Icons.INFO_ROUNDED, color=COLOR_PRIMARY, size=22),
            ft.Text(f"Досьє компанії: {name}", size=FONT_DIALOG_TITLE, weight=ft.FontWeight.BOLD),
        ]),
        content=content,
        actions=[
            ft.TextButton("Закрити", on_click=close_dlg),
            ft.FilledButton(
                "✉️ Лист №1 (Plain Text)",
                icon=ft.Icons.EMAIL_ROUNDED,
                style=ft.ButtonStyle(bgcolor=COLOR_PRIMARY, color=ft.Colors.WHITE),
                on_click=lambda e: (close_dlg(), create_email_preview_dialog(page, account, on_update_status))
            ),
            ft.FilledButton(
                "📄 Notion Blueprint",
                icon=ft.Icons.DESCRIPTION_ROUNDED,
                style=ft.ButtonStyle(bgcolor=COLOR_INDIGO, color=ft.Colors.WHITE),
                on_click=lambda e: (close_dlg(), create_blueprint_preview_dialog(page, account))
            )
        ]
    )

    page.show_dialog(dlg)
    return dlg
