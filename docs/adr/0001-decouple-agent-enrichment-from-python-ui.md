# ADR 0001: Decouple AI Agent Enrichment from Python UI

* **Status:** Accepted
* **Date:** 2026-10-15
* **Author:** Kiril Borysenko / AsyncFlow Systems
* **Technical Domain:** System Architecture / AI Agent Integration

---

## Context

In early architectural iterations, the Python desktop application directly bundled LLM orchestration SDKs (OpenAI, Gemini), web scraping libraries, and asynchronous enrichment pipelines within the local GUI process.

This design incurred several critical failure modes:
1. **Excessive SaaS API Costs:** Commercial data providers (Apollo, Hunter, Clearbit) demanded $300–$500/month in subscription credits for lead search and email pattern enrichment.
2. **Process Bloat and Thread Freezes:** Headless browsers (Selenium/Playwright) and unstable HTTP scrapers bloated local memory consumption (>1.2 GB RAM) and caused thread deadlock in the GUI event loop.
3. **Rigid Prompt-to-Code Coupling:** Iterating on cold outreach copy or research heuristics required continuous Python code edits, redeployments, and complex mocking during unit tests.

## Decision

We decided to **completely decouple the AI reasoning and enrichment pipeline from the Python UI runtime**:
1. **Autonomous AI Agent Skills (`.agent/skills/`):** Web discovery, deep company intelligence extraction via keyless markdown mirrors (e.g., `r.jina.ai`), and cold copy generation were moved to standalone Antigravity agent skills (`lead-enricher`, `instant-closer`).
2. **Lean Local-First Visual Core:** The Python application (`main.py`, Flet UI, `core/database.py`) was re-engineered as a dedicated, lightweight visual CRM dashboard and SQLite ACID-compliant persistence layer.
3. **Direct SQLite Data Contract:** Agent skills validate schemas and commit records directly into `data/leads.db` using standardized SQL queries, leaving the Python application 100% decoupled from LLM API keys and web scraping libraries.

```
┌───────────────────────────────────────┐       ┌───────────────────────────────────────┐
│     AI Agent Skills (.agent/skills/)  │       │       Python Visual Dashboard (Flet)  │
│  - instant-closer                     │       │  - Zero API Key dependency            │
│  - lead-enricher                      │       │  - Sub-second UI boot & filtering     │
│  - DNS/MX terminal verification       │       │  - Modal previews & status management │
└───────────────────┬───────────────────┘       └───────────────────▲───────────────────┘
                    │                                               │
                    │ Direct ACID SQLite Transactions               │ Local SQLite Read
                    ▼                                               │
             ┌─────────────────────────────────────────────────────────────┐
             │                   data/leads.db (SQLite)                    │
             └─────────────────────────────────────────────────────────────┘
```

## Rationale & Trade-offs

### Advantages
* **100% Cost Reduction ($0/month):** Eliminates recurring SaaS API fees by leveraging keyless markdown readers, terminal DNS lookups, and native agent execution.
* **Sub-Second Test & Startup Performance:** Removing heavy browser and cloud AI dependencies allows the full Python test suite (`unittest`) to complete in under 0.6 seconds.
* **Resilient Separation of Concerns:** If an external web source changes its HTML structure, only the modular agent skill is calibrated; the visual dashboard, database schema, and desktop app remain entirely unaffected.
* **Zero-Leak Security:** The visual application can run entirely offline or in air-gapped environments without holding commercial API keys.

### Trade-offs
* **Out-of-Process Execution:** Data collection is invoked via agent workflows or CLI rather than clicking a button inside the Python GUI. This deliberate constraint ensures production stability and prevents uncontrolled LLM credit burning.

## Consequences

* The Python dependency tree was reduced to the core desktop UI and schema validation packages (`flet`, `pydantic`, `sqlite3`).
* The SQLite database serves as the unambiguous, ACID-compliant single source of truth.
* All future agent features (e.g., inbox simulation and copy revision) are implemented as isolated agent skills rather than Python GUI modules.
