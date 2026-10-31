"""
Header navigation bar for B2B Lead Intelligence Dashboard.
Displays application title, real-time database telemetry counters (inboxes, statuses), and refresh action.
"""

import flet as ft
from ui.theme import (
    FONT_HEADER_TITLE,
    FONT_CAPTION,
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

class DashboardHeader(ft.Container):
    def __init__(self, accounts: list, on_refresh):
        super().__init__(
            bgcolor=BG_SURFACE,
            padding=ft.Padding.symmetric(horizontal=24, vertical=14),
            border=ft.Border(bottom=ft.BorderSide(1, BORDER_COLOR)),
        )
        self.accounts = accounts
        self.on_refresh = on_refresh
        self.build_ui()

    def update_metrics(self, accounts: list):
        self.accounts = accounts
        self.build_ui()
        try:
            self.update()
        except Exception:
            pass

    def build_ui(self):
        total = len(self.accounts)
        inbox_1 = sum(1 for a in self.accounts if a.get("inbox_slot") in ("Inbox 1", "Пошта 1"))
        inbox_2 = sum(1 for a in self.accounts if a.get("inbox_slot") in ("Inbox 2", "Пошта 2"))
        verified = sum(1 for a in self.accounts if a.get("is_verified_live") or "Verified" in a.get("mx_status", ""))
        not_sent = sum(1 for a in self.accounts if (a.get("status") or a.get("outreach_status") or "Draft") in ("Draft", "Не відправлено"))
        sent = sum(1 for a in self.accounts if (a.get("status") or a.get("outreach_status")) in ("Sent", "Відправлено"))
        replied = sum(1 for a in self.accounts if (a.get("status") or a.get("outreach_status")) in ("Replied", "Отримано відповідь", "Відповіли"))

        # Metric Badges
        metric_badges = ft.Row([
            self._metric_badge("Total", str(total), COLOR_PRIMARY, COLOR_PRIMARY_LIGHT, ft.Icons.FOLDER_SPECIAL_ROUNDED),
            self._metric_badge("Inbox 1 (10/d)", str(inbox_1), COLOR_INDIGO, COLOR_INDIGO_LIGHT, ft.Icons.MARK_EMAIL_READ_ROUNDED),
            self._metric_badge("Inbox 2 (10/d)", str(inbox_2), COLOR_INDIGO, COLOR_INDIGO_LIGHT, ft.Icons.ALL_INBOX_ROUNDED),
            self._metric_badge("MX Live", str(verified), COLOR_SUCCESS, COLOR_SUCCESS_LIGHT, ft.Icons.VERIFIED_ROUNDED),
            self._metric_badge("Draft", str(not_sent), COLOR_WARNING, COLOR_WARNING_LIGHT, ft.Icons.SCHEDULE_ROUNDED),
            self._metric_badge("Sent", str(sent), COLOR_PRIMARY, COLOR_PRIMARY_LIGHT, ft.Icons.SEND_ROUNDED),
            self._metric_badge("Replied", str(replied), COLOR_SUCCESS, COLOR_SUCCESS_LIGHT, ft.Icons.MARK_CHAT_READ_ROUNDED),
        ], spacing=8, wrap=True)

        self.content = ft.Row([
            # Title & Subtitle
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.AUTO_GRAPH_ROUNDED, color=ft.Colors.WHITE, size=22),
                    bgcolor=COLOR_PRIMARY,
                    border_radius=8,
                    padding=8
                ),
                ft.Column([
                    ft.Text("B2B Lead Intelligence Dashboard", size=FONT_HEADER_TITLE, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text("AI Agentic Intelligence • 20 leads/day • Autonomous Process Automation Showcase", size=FONT_CAPTION, color=TEXT_MUTED),
                ], spacing=2)
            ], spacing=12),

            ft.Container(expand=True),

            # Metric chips
            metric_badges,

            ft.Container(width=10),

            # Refresh Button
            ft.FilledButton(
                "Refresh",
                icon=ft.Icons.REFRESH_ROUNDED,
                style=ft.ButtonStyle(
                    bgcolor=COLOR_PRIMARY_LIGHT,
                    color=COLOR_PRIMARY,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=10)
                ),
                on_click=lambda e: self.on_refresh()
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _metric_badge(self, label: str, val: str, color: str, bgcolor: str, icon):
        return ft.Container(
            bgcolor=bgcolor,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=9, vertical=5),
            content=ft.Row([
                ft.Icon(icon, size=15, color=color),
                ft.Text(f"{label}:", size=FONT_CAPTION, color=TEXT_SECONDARY),
                ft.Text(val, size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=color),
            ], spacing=4)
        )
