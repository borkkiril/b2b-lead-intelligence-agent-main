#!/usr/bin/env python3
"""
Web Demo Showcase Generator for GitHub Pages.
Exports SQLite database (data/ci_demo.db or data/leads.db) into a self-contained,
interactive, single-file HTML/CSS/JS dashboard (dist/index.html).

Adheres strictly to ui/theme.py design tokens:
- Clean light theme (#FFFFFF, #F8FAFC, #0F172A, #2563EB, #059669, #4F46E5)
- Real-time client-side search, status & country filtering
- Clickable modals for Plain-Text Email (#1 & #1.5) and Notion Architecture Blueprint
- Responsive desktop & mobile layout with zero external dependencies
"""

import os
import sys
import json
import sqlite3
import argparse

ROOT = os.path.dirname(os.path.abspath(__file__))

def get_leads_from_db(db_path: str) -> list:
    """Reads leads from SQLite database."""
    if not os.path.exists(db_path):
        # Fallback to default leads.db if ci_demo.db not found
        fallback = os.path.join(ROOT, "data", "leads.db")
        if os.path.exists(fallback):
            db_path = fallback
        else:
            raise FileNotFoundError(f"Database not found at {db_path} or {fallback}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY id ASC;")
    rows = cursor.fetchall()
    leads = [dict(r) for r in rows]
    conn.close()
    return leads

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Orion — B2B Lead Intelligence Dashboard (Live Interactive Demo)</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%232563EB'><path d='M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5'/></svg>">
  <style>
    :root {
      --bg-page: #FFFFFF;
      --bg-surface: #FFFFFF;
      --bg-card: #F8FAFC;
      --bg-card-hover: #F1F5F9;
      --border-color: #E2E8F0;
      --text-primary: #0F172A;
      --text-secondary: #334155;
      --text-muted: #64748B;
      --color-primary: #2563EB;
      --color-primary-light: #EFF6FF;
      --color-success: #059669;
      --color-success-light: #ECFDF5;
      --color-warning: #D97706;
      --color-warning-light: #FFFBEB;
      --color-danger: #DC2626;
      --color-danger-light: #FEF2F2;
      --color-indigo: #4F46E5;
      --color-indigo-light: #EEF2FF;
      --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--font-family);
      background-color: #F8FAFC;
      color: var(--text-primary);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* TOP HEADER */
    header {
      background: var(--bg-surface);
      border-bottom: 1px solid var(--border-color);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      z-index: 10;
    }

    .brand-group {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-logo {
      width: 38px;
      height: 38px;
      background: var(--color-primary-light);
      color: var(--color-primary);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      font-weight: bold;
    }

    .brand-title {
      font-size: 16px;
      font-weight: 700;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .brand-subtitle {
      font-size: 12px;
      color: var(--text-muted);
    }

    .badge-live-demo {
      background: #10B981;
      color: #fff;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .metrics-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .metric-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      border: 1px solid transparent;
      transition: all 0.2s;
    }

    .metric-total { background: var(--color-primary-light); color: var(--color-primary); border-color: #DBEAFE; }
    .metric-inbox1 { background: var(--color-indigo-light); color: var(--color-indigo); border-color: #E0E7FF; }
    .metric-inbox2 { background: var(--color-indigo-light); color: var(--color-indigo); border-color: #E0E7FF; }
    .metric-mxlive { background: var(--color-success-light); color: var(--color-success); border-color: #D1FAE5; }
    .metric-notsent { background: var(--color-warning-light); color: var(--color-warning); border-color: #FEF3C7; }
    .metric-sent { background: var(--color-primary-light); color: var(--color-primary); border-color: #DBEAFE; }
    .metric-replied { background: var(--color-success-light); color: var(--color-success); border-color: #A7F3D0; }

    /* LAYOUT: SIDEBAR + MAIN VIEW */
    .app-container {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    aside {
      width: 290px;
      background: var(--bg-surface);
      border-right: 1px solid var(--border-color);
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      overflow-y: auto;
    }

    .sidebar-section-title {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--text-muted);
      margin-bottom: 8px;
    }

    .search-box {
      width: 100%;
      padding: 10px 14px;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      font-size: 13px;
      color: var(--text-primary);
      outline: none;
      transition: border 0.2s;
    }
    .search-box:focus {
      border-color: var(--color-primary);
      background: #FFFFFF;
    }

    .filter-btn-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .filter-btn {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      border-radius: 6px;
      border: none;
      background: transparent;
      color: var(--text-secondary);
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
      text-align: left;
    }
    .filter-btn:hover {
      background: var(--bg-card-hover);
      color: var(--text-primary);
    }
    .filter-btn.active {
      background: var(--color-primary-light);
      color: var(--color-primary);
      font-weight: 600;
    }
    .filter-count {
      font-size: 11px;
      padding: 2px 6px;
      border-radius: 10px;
      background: #E2E8F0;
      color: var(--text-secondary);
    }
    .filter-btn.active .filter-count {
      background: var(--color-primary);
      color: #fff;
    }

    .tech-stack-card {
      margin-top: auto;
      background: #F8FAFC;
      border: 1px dashed var(--border-color);
      border-radius: 8px;
      padding: 12px;
      font-size: 11px;
      color: var(--text-muted);
      line-height: 1.5;
    }
    .tech-stack-card strong {
      color: var(--text-secondary);
    }

    /* MAIN CONTENT */
    main {
      flex: 1;
      padding: 20px 24px;
      overflow-y: auto;
      background: #F8FAFC;
    }

    .lead-list {
      display: flex;
      flex-direction: column;
      gap: 14px;
      max-width: 1300px;
      margin: 0 auto;
    }

    /* LEAD CARD */
    .lead-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 16px 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
      transition: transform 0.15s, box-shadow 0.15s;
    }
    .lead-card:hover {
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
      border-color: #CBD5E1;
    }

    .card-header-row {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }

    .lead-index {
      font-size: 14px;
      font-weight: 700;
      color: var(--text-muted);
    }

    .lead-company {
      font-size: 16px;
      font-weight: 700;
      color: var(--text-primary);
    }

    .tag-badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
    }
    .tag-inbox { background: var(--color-primary-light); color: var(--color-primary); }
    .tag-country { background: var(--color-indigo-light); color: var(--color-indigo); }
    .tag-mx { background: var(--color-success-light); color: var(--color-success); }

    .card-actions-right {
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn-action {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s;
      text-decoration: none;
    }
    .btn-web {
      background: transparent;
      color: var(--color-primary);
      border-color: transparent;
    }
    .btn-web:hover { background: var(--color-primary-light); }

    .btn-email-preview {
      background: var(--color-primary-light);
      color: var(--color-primary);
      border-color: #BFDBFE;
    }
    .btn-email-preview:hover {
      background: var(--color-primary);
      color: #fff;
    }

    .btn-blueprint-preview {
      background: var(--color-indigo-light);
      color: var(--color-indigo);
      border-color: #C7D2FE;
    }
    .btn-blueprint-preview:hover {
      background: var(--color-indigo);
      color: #fff;
    }

    .btn-details {
      background: var(--bg-card);
      color: var(--text-secondary);
      border-color: var(--border-color);
      padding: 6px 9px;
    }
    .btn-details:hover {
      background: #E2E8F0;
      color: var(--text-primary);
    }

    .card-divider {
      border: none;
      border-top: 1px solid var(--border-color);
      margin-bottom: 12px;
    }

    .card-body-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 18px;
    }

    .problem-box-title {
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .problem-box-text {
      font-size: 13px;
      color: var(--text-primary);
      line-height: 1.5;
    }

    .contact-info-col {
      display: flex;
      flex-direction: column;
      gap: 6px;
      border-left: 1px solid var(--border-color);
      padding-left: 16px;
    }

    .info-row {
      font-size: 12px;
      color: var(--text-secondary);
      display: flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .info-row strong {
      color: var(--text-primary);
      min-width: 60px;
    }

    .status-select {
      margin-top: 4px;
      padding: 5px 8px;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      background: var(--bg-card);
      font-size: 12px;
      font-weight: 600;
      color: var(--text-primary);
      cursor: pointer;
      outline: none;
    }
    .status-select:focus {
      border-color: var(--color-primary);
    }

    /* MODAL WINDOWS */
    .modal-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.7);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 16px;
    }
    .modal-overlay.open {
      display: flex;
    }

    .modal-dialog {
      background: #FFFFFF !important;
      border: 1px solid var(--border-color);
      border-radius: 12px;
      width: 100%;
      max-width: 820px;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
      z-index: 1001;
      opacity: 1 !important;
    }

    .modal-header {
      padding: 16px 22px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .modal-title {
      font-size: 16px;
      font-weight: 700;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .modal-close-btn {
      background: transparent;
      border: none;
      font-size: 20px;
      color: var(--text-muted);
      cursor: pointer;
      line-height: 1;
      padding: 4px;
    }
    .modal-close-btn:hover { color: var(--text-primary); }

    .modal-body {
      padding: 20px 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.6;
    }

    .modal-footer {
      padding: 14px 22px;
      border-top: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
      background: var(--bg-card);
      border-bottom-left-radius: 12px;
      border-bottom-right-radius: 12px;
    }

    .content-box-email {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 14px;
    }
    .content-box-followup {
      background: var(--color-indigo-light);
      border: 1px solid #C7D2FE;
      border-radius: 8px;
      padding: 14px;
    }

    .email-pre {
      font-family: monospace;
      font-size: 13px;
      color: var(--text-primary);
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.6;
      margin-top: 8px;
    }

    .blueprint-markdown {
      font-size: 13px;
      line-height: 1.6;
      color: var(--text-primary);
    }
    .blueprint-markdown h1 { font-size: 18px; margin: 12px 0 8px; color: var(--color-indigo); }
    .blueprint-markdown h2 { font-size: 16px; margin: 12px 0 6px; }
    .blueprint-markdown h3 { font-size: 14px; margin: 10px 0 6px; color: var(--text-primary); }
    .blueprint-markdown code {
      background: #1E293B;
      color: #38BDF8;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
      font-size: 12px;
    }
    .blueprint-markdown pre {
      background: #0F172A;
      color: #F8FAFC;
      padding: 14px;
      border-radius: 8px;
      overflow-x: auto;
      font-family: monospace;
      font-size: 12px;
      margin: 10px 0;
      line-height: 1.5;
    }

    /* TOAST */
    #toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #0F172A;
      color: #fff;
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      display: none;
      align-items: center;
      gap: 8px;
      box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2);
      z-index: 2000;
    }
    #toast.show { display: flex; animation: toastIn 0.2s ease-out; }
    @keyframes toastIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

    @media (max-width: 900px) {
      .app-container { flex-direction: column; }
      aside { width: 100%; border-right: none; border-bottom: 1px solid var(--border-color); }
      .card-body-grid { grid-template-columns: 1fr; }
      .contact-info-col { border-left: none; padding-left: 0; border-top: 1px solid var(--border-color); padding-top: 10px; }
    }
  </style>
</head>
<body>

  <!-- HEADER -->
  <header>
    <div class="brand-group">
      <div class="brand-logo">⚡</div>
      <div>
        <div class="brand-title">
          Orion — B2B Lead Intelligence Dashboard
          <span class="badge-live-demo">Live GitHub Pages Demo</span>
        </div>
        <div class="brand-subtitle">AsyncFlow Systems • Production Lead Management (100% Zero-Cost Architecture)</div>
      </div>
    </div>

    <!-- METRICS -->
    <div class="metrics-row" id="metricsRow">
      <div class="metric-badge metric-total">📁 Всього: <span id="mTotal">0</span></div>
      <div class="metric-badge metric-inbox1">✉️ Пошта 1 (10/д): <span id="mInbox1">0</span></div>
      <div class="metric-badge metric-inbox2">📬 Пошта 2 (10/д): <span id="mInbox2">0</span></div>
      <div class="metric-badge metric-mxlive">🛡️ MX Live: <span id="mVerified">0</span></div>
      <div class="metric-badge metric-notsent">⏳ Не відправлено: <span id="mNotSent">0</span></div>
      <div class="metric-badge metric-sent">📤 Відправлено: <span id="mSent">0</span></div>
      <div class="metric-badge metric-replied">💬 Отримано відповідь: <span id="mReplied">0</span></div>
    </div>
  </header>

  <!-- APP CONTAINER -->
  <div class="app-container">
    <!-- SIDEBAR -->
    <aside>
      <div>
        <div class="sidebar-section-title">🔍 Пошук компанії</div>
        <input type="text" id="searchInput" class="search-box" placeholder="Введіть назву, сайт, проблему...">
      </div>

      <div>
        <div class="sidebar-section-title">📊 Статус аутрічу</div>
        <div class="filter-btn-group" id="statusFilterGroup">
          <button class="filter-btn active" data-status="Всі">Всі компанії <span class="filter-count" id="cAll">0</span></button>
          <button class="filter-btn" data-status="Не відправлено">⏳ Не відправлено <span class="filter-count" id="cNotSent">0</span></button>
          <button class="filter-btn" data-status="Відправлено">📤 Відправлено <span class="filter-count" id="cSent">0</span></button>
          <button class="filter-btn" data-status="Отримано відповідь">💬 Отримано відповідь <span class="filter-count" id="cReplied">0</span></button>
        </div>
      </div>

      <div>
        <div class="sidebar-section-title">🌍 Географія (Ринок)</div>
        <div class="filter-btn-group" id="countryFilterGroup">
          <button class="filter-btn active" data-country="Всі">Всі регіони</button>
          <button class="filter-btn" data-country="ЄС">🇪🇺 Європейський Союз</button>
          <button class="filter-btn" data-country="UK">🇬🇧 Велика Британія</button>
          <button class="filter-btn" data-country="Україна">🇺🇦 Україна</button>
        </div>
      </div>

      <div>
        <div class="sidebar-section-title">📬 Скринька відправки</div>
        <div class="filter-btn-group" id="inboxFilterGroup">
          <button class="filter-btn active" data-inbox="Всі">Всі скриньки</button>
          <button class="filter-btn" data-inbox="Пошта 1">Пошта 1 (UK / ЄС)</button>
          <button class="filter-btn" data-inbox="Пошта 2">Пошта 2 (UA / ЄС)</button>
        </div>
      </div>

      <div class="tech-stack-card">
        <strong>⚡ Zero-Cost Architecture</strong><br>
        100% Offline SQLite ACID persistence layer with Flet (Flutter/Python) & Pydantic validation. Zero external API subscription fees.
      </div>
    </aside>

    <!-- MAIN VIEW -->
    <main>
      <div class="lead-list" id="leadList">
        <!-- Rendered by JavaScript -->
      </div>
    </main>
  </div>

  <!-- MODAL: EMAIL PREVIEW -->
  <div class="modal-overlay" id="emailModal">
    <div class="modal-dialog">
      <div class="modal-header">
        <div class="modal-title" id="emailModalTitle">✉️ Лист №1: Plain Text</div>
        <button class="modal-close-btn" onclick="closeModal('emailModal')">&times;</button>
      </div>
      <div class="modal-body">
        <div class="content-box-email">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong>✉️ Лист №1: Plain Text (День 1, без посилань, вхід через проблему Х):</strong>
            <button class="btn-action btn-email-preview" onclick="copyEmailBody()">📋 Скопіювати Лист №1</button>
          </div>
          <div class="email-pre" id="emailModalText1"></div>
        </div>

        <div class="content-box-followup">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:var(--color-indigo);">🔄 Лист №1.5: Follow-up (Staging Sandbox + $20k гарантія):</strong>
            <button class="btn-action btn-blueprint-preview" onclick="copyFollowupBody()">📋 Скопіювати Follow-up</button>
          </div>
          <div class="email-pre" id="emailModalText2"></div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-action btn-details" onclick="closeModal('emailModal')">Закрити</button>
        <button class="btn-action" style="background:var(--color-success); color:#fff;" onclick="markEmailSentFromModal()">
          ✓ Скопіювати та позначити 'Відправлено'
        </button>
      </div>
    </div>
  </div>

  <!-- MODAL: NOTION BLUEPRINT -->
  <div class="modal-overlay" id="blueprintModal">
    <div class="modal-dialog">
      <div class="modal-header">
        <div class="modal-title" id="blueprintModalTitle">📄 Notion Architecture Blueprint</div>
        <button class="modal-close-btn" onclick="closeModal('blueprintModal')">&times;</button>
      </div>
      <div class="modal-body">
        <div class="blueprint-markdown" id="blueprintModalContent"></div>
      </div>
      <div class="modal-footer">
        <button class="btn-action btn-details" onclick="closeModal('blueprintModal')">Закрити</button>
        <button class="btn-action btn-blueprint-preview" onclick="copyBlueprintBody()">📋 Скопіювати Notion Blueprint</button>
      </div>
    </div>
  </div>

  <!-- MODAL: ACCOUNT DETAILS -->
  <div class="modal-overlay" id="detailsModal">
    <div class="modal-dialog">
      <div class="modal-header">
        <div class="modal-title" id="detailsModalTitle">ℹ️ Повне досьє компанії</div>
        <button class="modal-close-btn" onclick="closeModal('detailsModal')">&times;</button>
      </div>
      <div class="modal-body" id="detailsModalContent">
      </div>
      <div class="modal-footer">
        <button class="btn-action btn-details" onclick="closeModal('detailsModal')">Закрити</button>
      </div>
    </div>
  </div>

  <!-- TOAST NOTIFICATION -->
  <div id="toast">✅ Повідомлення скопійовано в буфер обміну!</div>

  <script>
    // Embedded Data injected directly from SQLite
    let LEADS_DATA = /* [[DATA_PLACEHOLDER]] */;

    let currentFilter = {
      search: "",
      status: "Всі",
      country: "Всі",
      inbox: "Всі"
    };

    let activeModalLead = null;

    function renderMetrics() {
      const total = LEADS_DATA.length;
      const inbox1 = LEADS_DATA.filter(l => l.inbox_slot === "Пошта 1").length;
      const inbox2 = LEADS_DATA.filter(l => l.inbox_slot === "Пошта 2").length;
      const verified = LEADS_DATA.filter(l => (l.mx_status || "").includes("Verified")).length;
      const notSent = LEADS_DATA.filter(l => l.status === "Не відправлено").length;
      const sent = LEADS_DATA.filter(l => l.status === "Відправлено").length;
      const replied = LEADS_DATA.filter(l => l.status === "Отримано відповідь").length;

      document.getElementById("mTotal").innerText = total;
      document.getElementById("mInbox1").innerText = inbox1;
      document.getElementById("mInbox2").innerText = inbox2;
      document.getElementById("mVerified").innerText = verified;
      document.getElementById("mNotSent").innerText = notSent;
      document.getElementById("mSent").innerText = sent;
      document.getElementById("mReplied").innerText = replied;

      document.getElementById("cAll").innerText = total;
      document.getElementById("cNotSent").innerText = notSent;
      document.getElementById("cSent").innerText = sent;
      document.getElementById("cReplied").innerText = replied;
    }

    function matchesFilter(lead) {
      if (currentFilter.status !== "Всі" && lead.status !== currentFilter.status) return false;
      if (currentFilter.inbox !== "Всі" && lead.inbox_slot !== currentFilter.inbox) return false;

      if (currentFilter.country !== "Всі") {
        const c = (lead.country || "").toLowerCase();
        if (currentFilter.country === "ЄС") {
          const euList = ["germany", "німеччин", "france", "франц", "netherlands", "poland", "польщ", "ireland", "estonia", "sweden", "spain", "italy", "austria", "belgium", "єс", "eu"];
          if (!euList.some(k => c.includes(k))) return false;
        } else if (currentFilter.country === "UK") {
          const ukList = ["uk", "united kingdom", "london", "великобритан", "лондон", "england"];
          if (!ukList.some(k => c.includes(k))) return false;
        } else if (currentFilter.country === "Україна") {
          const uaList = ["ukraine", "україна", "kyiv", "київ", "lviv", "львів"];
          if (!uaList.some(k => c.includes(k))) return false;
        }
      }

      if (currentFilter.search) {
        const q = currentFilter.search.toLowerCase();
        const haystack = `${lead.company} ${lead.website} ${lead.country} ${lead.industry_problem_x} ${lead.contact_role} ${lead.verified_email}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }

      return true;
    }

    function renderLeads() {
      const container = document.getElementById("leadList");
      container.innerHTML = "";

      const filtered = LEADS_DATA.filter(matchesFilter);

      if (filtered.length === 0) {
        container.innerHTML = `
          <div style="text-align:center; padding: 60px 20px; background:var(--bg-surface); border:1px solid var(--border-color); border-radius:10px;">
            <div style="font-size:36px; margin-bottom:10px;">🔍</div>
            <div style="font-size:16px; font-weight:700; color:var(--text-primary); margin-bottom:6px;">Не знайдено жодної компанії</div>
            <div style="font-size:13px; color:var(--text-muted);">Спробуйте змінити критерії фільтрації у бічній панелі.</div>
          </div>
        `;
        return;
      }

      filtered.forEach((lead, idx) => {
        const card = document.createElement("div");
        card.className = "lead-card";
        card.innerHTML = `
          <div class="card-header-row">
            <span class="lead-index">#${lead.id}</span>
            <span class="lead-company">${escapeHtml(lead.company)}</span>
            <span class="tag-badge tag-inbox">✉️ ${escapeHtml(lead.inbox_slot)}</span>
            <span class="tag-badge tag-country">${escapeHtml(lead.country)}</span>
            <span class="tag-badge tag-mx">🛡️ ${escapeHtml(lead.mx_status)}</span>

            <div class="card-actions-right">
              ${lead.website ? `<a href="https://${escapeHtml(lead.website.replace(/^https?:\\/\\//, ''))}" target="_blank" class="btn-action btn-web">🌐 ${escapeHtml(lead.website)}</a>` : ''}
              <button class="btn-action btn-email-preview" onclick="openEmailModal(${lead.id})">✉️ Лист №1 (Plain)</button>
              <button class="btn-action btn-blueprint-preview" onclick="openBlueprintModal(${lead.id})">📄 Notion Блюпринт</button>
              <button class="btn-action btn-details" onclick="openDetailsModal(${lead.id})" title="Повне досьє">ℹ️</button>
            </div>
          </div>

          <hr class="card-divider">

          <div class="card-body-grid">
            <div>
              <div class="problem-box-title">⚡ Галузева проблема Х (Операційне вузьке місце):</div>
              <div class="problem-box-text">${escapeHtml(lead.industry_problem_x)}</div>
            </div>

            <div class="contact-info-col">
              <div class="info-row"><strong>👤 ЛПР:</strong> <span>${escapeHtml(lead.contact_role)}</span></div>
              <div class="info-row"><strong>✉️ Email:</strong> <span>${escapeHtml(lead.verified_email)}</span></div>
              <div class="info-row" style="margin-top:2px;">
                <strong>📊 Статус:</strong>
                <select class="status-select" onchange="updateLeadStatus(${lead.id}, this.value)">
                  <option value="Не відправлено" ${lead.status === "Не відправлено" ? "selected" : ""}>⏳ Не відправлено</option>
                  <option value="Відправлено" ${lead.status === "Відправлено" ? "selected" : ""}>📤 Відправлено</option>
                  <option value="Отримано відповідь" ${lead.status === "Отримано відповідь" ? "selected" : ""}>💬 Отримано відповідь</option>
                </select>
              </div>
            </div>
          </div>
        `;
        container.appendChild(card);
      });
    }

    function updateLeadStatus(id, newStatus) {
      const lead = LEADS_DATA.find(l => l.id === id);
      if (lead) {
        lead.status = newStatus;
        renderMetrics();
        showToast(`Статус ${lead.company} змінено на "${newStatus}"!`);
      }
    }

    function openEmailModal(id) {
      const lead = LEADS_DATA.find(l => l.id === id);
      if (!lead) return;
      activeModalLead = lead;

      document.getElementById("emailModalTitle").innerText = `✉️ Лист №1: ${lead.company}`;
      document.getElementById("emailModalText1").innerText = lead.email_step1_plain_text || "";
      document.getElementById("emailModalText2").innerText = lead.email_step1_5_followup || "";

      document.getElementById("emailModal").classList.add("open");
    }

    function openBlueprintModal(id) {
      const lead = LEADS_DATA.find(l => l.id === id);
      if (!lead) return;
      activeModalLead = lead;

      document.getElementById("blueprintModalTitle").innerText = `📄 Notion Architecture Blueprint: ${lead.company}`;
      document.getElementById("blueprintModalContent").innerHTML = formatMarkdown(lead.notion_adaptation_blueprint || "");

      document.getElementById("blueprintModal").classList.add("open");
    }

    function openDetailsModal(id) {
      const lead = LEADS_DATA.find(l => l.id === id);
      if (!lead) return;
      activeModalLead = lead;

      document.getElementById("detailsModalTitle").innerText = `ℹ️ Досьє: ${lead.company}`;
      document.getElementById("detailsModalContent").innerHTML = `
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px;">
          <div><strong>Компанія:</strong> ${escapeHtml(lead.company)}</div>
          <div><strong>Сайт:</strong> <a href="https://${escapeHtml(lead.website)}" target="_blank">${escapeHtml(lead.website)}</a></div>
          <div><strong>Країна:</strong> ${escapeHtml(lead.country)}</div>
          <div><strong>Скринька:</strong> ${escapeHtml(lead.inbox_slot)}</div>
          <div><strong>ЛПР:</strong> ${escapeHtml(lead.contact_role)}</div>
          <div><strong>Email:</strong> ${escapeHtml(lead.verified_email)}</div>
          <div><strong>MX Статус:</strong> ${escapeHtml(lead.mx_status)}</div>
          <div><strong>Поточний статус:</strong> ${escapeHtml(lead.status)}</div>
        </div>
        <div style="margin-top:10px;">
          <strong>Операційне вузьке місце:</strong>
          <p style="margin-top:4px; padding:10px; background:var(--bg-card); border-radius:6px; border:1px solid var(--border-color);">${escapeHtml(lead.industry_problem_x)}</p>
        </div>
      `;
      document.getElementById("detailsModal").classList.add("open");
    }

    function closeModal(modalId) {
      document.getElementById(modalId).classList.remove("open");
    }

    function copyEmailBody() {
      if (activeModalLead) {
        copyText(activeModalLead.email_step1_plain_text || "", "Лист №1 скопійовано в буфер!");
      }
    }

    function copyFollowupBody() {
      if (activeModalLead) {
        copyText(activeModalLead.email_step1_5_followup || "", "Follow-up скопійовано в буфер!");
      }
    }

    function copyBlueprintBody() {
      if (activeModalLead) {
        copyText(activeModalLead.notion_adaptation_blueprint || "", "Notion Blueprint скопійовано в буфер!");
      }
    }

    function markEmailSentFromModal() {
      if (activeModalLead) {
        copyText(activeModalLead.email_step1_plain_text || "", "Лист скопійовано та статус змінено на 'Відправлено'!");
        updateLeadStatus(activeModalLead.id, "Відправлено");
        renderLeads();
        closeModal("emailModal");
      }
    }

    function copyText(text, msg) {
      navigator.clipboard.writeText(text).then(() => {
        showToast(msg);
      }).catch(() => {
        showToast(msg);
      });
    }

    function showToast(msg) {
      const toast = document.getElementById("toast");
      toast.innerText = `✅ ${msg}`;
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), 2500);
    }

    function escapeHtml(str) {
      if (!str) return "";
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function formatMarkdown(md) {
      if (!md) return "";
      let html = escapeHtml(md);

      // Code blocks
      html = html.replace(/```python([\\s\\S]*?)```/g, function(match, code) {
        return '<pre><code>' + code.trim() + '</code></pre>';
      });

      // Headers
      html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
      html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
      html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

      // Bold & Italic
      html = html.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
      html = html.replace(/\\*(.*?)\\*/g, '<em>$1</em>');

      // Unordered lists
      html = html.replace(/^\\- (.*$)/gim, '<li style="margin-left:20px;">$1</li>');

      // Line breaks
      html = html.replace(/\\n/g, '<br>');
      return html;
    }

    // Event listeners
    document.getElementById("searchInput").addEventListener("input", (e) => {
      currentFilter.search = e.target.value.trim();
      renderLeads();
    });

    document.querySelectorAll("#statusFilterGroup .filter-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#statusFilterGroup .filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentFilter.status = btn.dataset.status;
        renderLeads();
      });
    });

    document.querySelectorAll("#countryFilterGroup .filter-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#countryFilterGroup .filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentFilter.country = btn.dataset.country;
        renderLeads();
      });
    });

    document.querySelectorAll("#inboxFilterGroup .filter-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("#inboxFilterGroup .filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentFilter.inbox = btn.dataset.inbox;
        renderLeads();
      });
    });

    // Close on overlay click
    document.querySelectorAll(".modal-overlay").forEach(overlay => {
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) overlay.classList.remove("open");
      });
    });

    // Initial load
    renderMetrics();
    renderLeads();

    // Auto-open modal if specified in URL query params (e.g. ?modal=blueprint&id=1)
    const urlParams = new URLSearchParams(window.location.search);
    const modalParam = urlParams.get("modal");
    const idParam = parseInt(urlParams.get("id") || "1", 10);
    if (modalParam === "blueprint") {
      openBlueprintModal(idParam);
    } else if (modalParam === "email") {
      openEmailModal(idParam);
    }
  </script>
</body>
</html>
"""

def generate_web_showcase(db_path: str, output_path: str) -> str:
    """Generates dist/index.html from the given SQLite database."""
    leads = get_leads_from_db(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    json_data = json.dumps(leads, ensure_ascii=False, indent=2)
    rendered_html = HTML_TEMPLATE.replace("/* [[DATA_PLACEHOLDER]] */", json_data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    print(f"[SUCCESS] Exported {len(leads)} leads from {db_path} to {output_path} ({len(rendered_html)} bytes)!")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export SQLite leads database to standalone interactive HTML web showcase.")
    parser.add_argument("--db", type=str, default=os.path.join(ROOT, "data", "ci_demo.db"), help="Source SQLite database.")
    parser.add_argument("--out", type=str, default=os.path.join(ROOT, "dist", "index.html"), help="Destination HTML file.")
    args = parser.parse_args()

    generate_web_showcase(db_path=args.db, output_path=args.out)
