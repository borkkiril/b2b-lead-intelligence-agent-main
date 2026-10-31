# ADR 0003: Pre-LLM RODO/GDPR Compliance Guardrails and Multi-Server Operational Telemetry

* **Status:** Accepted
* **Date:** 2026-10-22
* **Author:** Kiril Borysenko / Orion Platform
* **Technical Domain:** AI Governance / Data Privacy (RODO/GDPR) / Multi-Server DevOps

---

## Context

Enterprise deployment of AI agents and automated B2B workflows introduces two critical engineering and regulatory challenges:

1. **Regulatory Data Privacy & RODO/GDPR Penalties:**
   European organizations operate under strict GDPR/RODO mandates. Transmitting unredacted personal identifiers—such as Polish PESEL numbers, National ID card numbers, private mobile telephone numbers, or consumer mailboxes (`@gmail.com`, `@wp.pl`, `@onet.pl`)—to third-party LLM cloud APIs directly violates GDPR Article 5(1)(c) (Data Minimization) and Article 6(1) (Lawfulness of Processing).

2. **Multi-Server Deployment Fragility & Silent Failures:**
   In distributed infrastructure environments with multi-server Linux instances, updating AI agent instances across heterogeneous nodes using manual SSH commands is error-prone. A schema mismatch, high SQLite lock contention, or degraded inference output can silently compromise production pipelines without automated telemetry and instant rollback mechanisms.

## Decision

We designed and implemented an integrated **Enterprise AI Governance and Operational Reliability Architecture**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    1. PRE-LLM RODO / GDPR COMPLIANCE GUARD                  │
│                     (core/rodo_compliance.py)                                │
│                                                                             │
│   Input Text / CV / Brief                                                   │
│      │                                                                      │
│      ├─► PESEL (11 digits) ─────────────► [REDACTED_PESEL_OR_ID]            │
│      ├─► Dowód Osobisty (3 letters+6d) ─► [REDACTED_PESEL_OR_ID]            │
│      ├─► Personal Phone Numbers ────────► [REDACTED_PHONE]                  │
│      ├─► Consumer Emails (@wp.pl, etc.) ─► [REDACTED_PRIVATE_EMAIL]          │
│      └─► Corporate B2B Entities ────────► PRESERVED (GDPR Art. 6(1)(f))     │
│                                                                             │
│   Sanitized Prompt ────────► Cloud LLM (Zero PII Exposure)                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│            2. MULTI-SERVER SSH DEPLOYMENT & TELEMETRY MONITORING             │
│            (deploy/ssh_multi_deploy.sh + core/health_monitor.py)            │
│                                                                             │
│   Local Machine: Unit Tests (<1s) ──► Node 1 / Node 2 (SSH)                │
│                                            │                                │
│                                            ├─► Atomic Backup (.tar.gz)      │
│                                            ├─► Git Pull & Pip Sync          │
│                                            ├─► Health Check: Latency < 45ms │
│                                            │   PRAGMA integrity_check == ok │
│                                            │   5-Gate AI Quality >= 7.0/10  │
│                                            ▼                                │
│                       Success ────────► Restart Service (systemctl)         │
│                       Failure ────────► Trap ERR: Automated Rollback        │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Pre-LLM Sanitization Layer (`core/rodo_compliance.py`):**
   * Deterministic regex pipeline executed before prompt construction.
   * Personal consumer domains are strictly blocked from outbound pipelines with structured audit records.
   * Legitimate B2B contacts are processed under GDPR Article 6(1)(f) (*Legitimate Business Interest*).

2. **Automated Health Telemetry (`core/health_monitor.py`):**
   * Real-time verification of SQLite database integrity (`PRAGMA integrity_check`).
   * Sub-millisecond latency telemetry for database read/write queries.
   * Automated 5-Gate scoring of AI-generated deliverables.
   * JSON alert payload generation for Slack / Webhook / PagerDuty notification upon metric degradation.

3. **Multi-Node Deployment with Rollback (`deploy/ssh_multi_deploy.sh`):**
   * Local pre-flight test gate ensures broken code never reaches remote servers.
   * Automated backup archive created on each remote node before code checkout.
   * Remote bash error trap (`trap rollback ERR`) automatically resets the git branch to the previous commit if health checks fail.

## Rationale & Trade-offs

### Advantages
* **Guaranteed RODO/GDPR Compliance:** Zero leakage of personal sensitive data to external LLM providers, ensuring audit-ready corporate governance.
* **Deterministic Execution:** Pre-LLM sanitization runs in pure Python with zero external API calls or network latency (<2ms).
* **High Availability & Zero Downtime:** The multi-server deployment script guarantees atomic rollback, preventing broken releases from remaining active on production nodes.
* **Measurable Quality SLA:** The 5-Gate quality scoring algorithm provides continuous quality assurance across all generated communication assets.

### Trade-offs
* **Maintenance of Consumer Domain Blacklist:** The list of consumer email providers requires periodic updates as new regional free webmail services emerge.
* **Conservative PII Masking:** Phone number regexes may occasionally mask 9-digit alphanumeric order IDs; this is mitigated by domain-specific boundary constraints.

## Consequences

* The platform satisfies corporate data governance standards required by enterprise European organizations.
* Multi-server deployment operations meet Linux systems engineering and DevOps automation criteria for distributed agent operations.
* All compliance decisions and health audit reports are stored as structured JSON artifacts for traceability.
