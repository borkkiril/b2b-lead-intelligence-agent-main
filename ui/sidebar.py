"""
Фільтри та панель налаштувань для B2B Lead Intelligence Dashboard.
Підтримує пошук, фільтрацію за статусом, країною та скринькою (Пошта 1 / Пошта 2).
"""

import flet as ft
from ui.theme import (
    FONT_BODY,
    FONT_CAPTION,
    BG_SURFACE,
    BG_CARD,
    BG_INPUT,
    BORDER_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    COLOR_PRIMARY,
    COLOR_PRIMARY_LIGHT,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_INDIGO,
    COLOR_INDIGO_LIGHT
)

class DashboardSidebar(ft.Container):
    def __init__(self, on_filter_change, current_status="Всі", current_country="Всі", current_inbox="Всі"):
        super().__init__(
            width=280,
            bgcolor=BG_SURFACE,
            padding=16,
            border=ft.Border(right=ft.BorderSide(1, BORDER_COLOR)),
        )
        self.on_filter_change = on_filter_change
        self.current_status = current_status
        self.current_country = current_country
        self.current_inbox = current_inbox
        self.search_query = ""
        self.build_ui()

    def build_ui(self):
        # 1. Search Box
        search_box = ft.TextField(
            hint_text="Пошук компанії чи ОПР...",
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            dense=True,
            text_size=FONT_BODY,
            bgcolor=BG_INPUT,
            border_color=BORDER_COLOR,
            border_radius=8,
            on_change=self._handle_search
        )

        # 2. Inbox Slot Selector (Пошта 1 / Пошта 2)
        inbox_options = ["Всі", "Пошта 1", "Пошта 2"]
        inbox_chips = []
        for ib in inbox_options:
            is_active = (self.current_inbox == ib)
            chip = ft.Container(
                content=ft.Text(
                    ib,
                    size=FONT_CAPTION,
                    weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                    color=COLOR_INDIGO if is_active else TEXT_SECONDARY
                ),
                bgcolor=COLOR_INDIGO_LIGHT if is_active else BG_CARD,
                border=ft.Border.all(1, COLOR_INDIGO if is_active else BORDER_COLOR),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                on_click=lambda e, ib_name=ib: self._handle_inbox_click(ib_name)
            )
            inbox_chips.append(chip)

        # 3. Status Filters
        status_items = [
            ("Всі", ft.Icons.ALL_INCLUSIVE_ROUNDED, COLOR_PRIMARY),
            ("Не відправлено", ft.Icons.SCHEDULE_ROUNDED, COLOR_WARNING),
            ("Відправлено", ft.Icons.SEND_ROUNDED, COLOR_INDIGO),
            ("Отримано відповідь", ft.Icons.MARK_CHAT_READ_ROUNDED, COLOR_SUCCESS),
        ]
        status_buttons = []
        for st_name, icon, color in status_items:
            is_active = (self.current_status == st_name)
            btn = ft.Container(
                content=ft.Row([
                    ft.Icon(icon, size=18, color=color if is_active else TEXT_MUTED),
                    ft.Text(
                        st_name,
                        size=FONT_BODY,
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                        color=color if is_active else TEXT_PRIMARY
                    )
                ], spacing=10),
                bgcolor=COLOR_PRIMARY_LIGHT if is_active else ft.Colors.TRANSPARENT,
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                on_click=lambda e, s=st_name: self._handle_status_click(s)
            )
            status_buttons.append(btn)

        # 4. Country Filters
        countries = ["Всі", "ЄС", "UK", "Україна"]
        country_chips = []
        for c in countries:
            is_active = (self.current_country == c)
            chip = ft.Container(
                content=ft.Text(
                    c,
                    size=FONT_CAPTION,
                    weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                    color=COLOR_PRIMARY if is_active else TEXT_SECONDARY
                ),
                bgcolor=COLOR_PRIMARY_LIGHT if is_active else BG_CARD,
                border=ft.Border.all(1, COLOR_PRIMARY if is_active else BORDER_COLOR),
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                on_click=lambda e, c_name=c: self._handle_country_click(c_name)
            )
            country_chips.append(chip)

        # 5. Protocol Card
        protocol_box = ft.Container(
            bgcolor=COLOR_INDIGO_LIGHT,
            border=ft.Border.all(1, COLOR_INDIGO),
            border_radius=8,
            padding=10,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SECURITY_ROUNDED, color=COLOR_INDIGO, size=16),
                    ft.Text("2-Step No-Link Протокол", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=COLOR_INDIGO)
                ], spacing=4),
                ft.Text("• 2 скриньки × 10 листів = 20/день", size=FONT_CAPTION, color=TEXT_PRIMARY),
                ft.Text("• Лист №1: Тільки Plain Text (без посилань)", size=FONT_CAPTION, color=TEXT_PRIMARY),
                ft.Text("• Лист №2: Notion Blueprint + 10x ROI", size=FONT_CAPTION, color=TEXT_PRIMARY),
                ft.Text("• Zero-Meeting: $2,000 аудит за 5 днів", size=FONT_CAPTION, color=TEXT_PRIMARY),
            ], spacing=3)
        )

        self.content = ft.Column([
            ft.Text("ШВИДКИЙ ПОШУК", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
            search_box,
            ft.Divider(height=12, color=BORDER_COLOR),

            ft.Text("СКРИНЬКА ВІДПРАВКИ", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
            ft.Row(inbox_chips, wrap=True, spacing=6),
            ft.Divider(height=12, color=BORDER_COLOR),

            ft.Text("СТАТУС АУТРІЧУ", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
            ft.Column(status_buttons, spacing=2),
            ft.Divider(height=12, color=BORDER_COLOR),

            ft.Text("РЕГІОН", size=FONT_CAPTION, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
            ft.Row(country_chips, wrap=True, spacing=6),
            ft.Divider(height=12, color=BORDER_COLOR),

            ft.Container(expand=True),

            protocol_box
        ], spacing=8)

    def _trigger_filter_change(self):
        self.on_filter_change(self.search_query, self.current_status, self.current_country, self.current_inbox)

    def _handle_search(self, e):
        self.search_query = e.control.value
        self._trigger_filter_change()

    def _handle_inbox_click(self, inbox: str):
        self.current_inbox = inbox
        self.build_ui()
        try:
            self.update()
        except Exception:
            pass
        self._trigger_filter_change()

    def _handle_status_click(self, status: str):
        self.current_status = status
        self.build_ui()
        try:
            self.update()
        except Exception:
            pass
        self._trigger_filter_change()

    def _handle_country_click(self, country: str):
        self.current_country = country
        self.build_ui()
        try:
            self.update()
        except Exception:
            pass
        self._trigger_filter_change()
