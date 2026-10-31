# ADR 0003: Pre-LLM RODO/GDPR Data Minimization & Privacy Guardrails

* **Status:** Accepted
* **Date:** 2026-10-22
* **Author:** Kiril Borysenko / Orion Platform
* **Technical Domain:** AI Governance / Data Privacy (RODO/GDPR) / Data Minimization

---

## Context

Enterprise deployment of AI agents in commercial business workflows introduces critical regulatory and privacy requirements under European Union law:

1. **Regulatory Data Privacy & RODO/GDPR Mandates:**
   European organizations operate under strict GDPR/RODO mandates. Transmitting unredacted personal identifiers—such as Polish PESEL numbers, National ID card numbers, private mobile telephone numbers, or consumer mailboxes (`@gmail.com`, `@wp.pl`, `@onet.pl`)—to third-party LLM cloud APIs directly violates GDPR Article 5(1)(c) (*Data Minimization*) and Article 6(1) (*Lawfulness of Processing*).

2. **Accidental Consumer Contact Risks:**
   Outbound B2B communication pipelines must strictly avoid contacting private consumer mailboxes. Contacting consumers on personal webmail addresses exposes sender domains to regulatory complaints and spam reporting.

## Decision

We designed and implemented a deterministic **Pre-LLM RODO / GDPR Data Minimization Guardrail Layer** (`core/rodo_compliance.py`):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PRE-LLM RODO / GDPR COMPLIANCE GUARD                     │
│                         (core/rodo_compliance.py)                            │
│                                                                             │
│   Input Text / Lead Record / Brief                                          │
│      │                                                                      │
│      ├─► PESEL (11 digits) ─────────────► [REDACTED_PESEL_OR_ID]            │
│      ├─► Dowód Osobisty (3 letters+6d) ─► [REDACTED_PESEL_OR_ID]            │
│      ├─► Personal Phone Numbers ────────► [REDACTED_PHONE]                  │
│      ├─► Consumer Emails (@wp.pl, etc.) ─► [REDACTED_PRIVATE_EMAIL]          │
│      └─► Corporate B2B Entities ────────► PRESERVED (GDPR Art. 6(1)(f))     │
│                                                                             │
│   Sanitized Prompt / Record ────► Cloud LLM (Zero Sensitive PII Exposure)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Pre-LLM Sanitization Pipeline:**
   * Deterministic regex pipeline executed prior to prompt construction or model inference.
   * Personal consumer domains are strictly identified and blocked from outbound pipelines with structured compliance audit records.
   * Legitimate corporate B2B touchpoints are verified and processed under GDPR Article 6(1)(f) (*Legitimate Business Interest*).

2. **Automated Compliance Verification:**
   * Unit tests in `tests/test_system.py` deterministically verify PII redaction across test payloads with zero network calls.
   * Lead records are audited for consumer domain presence before database persistence.

## Rationale & Trade-offs

### Advantages
* **Guaranteed RODO/GDPR Compliance:** Zero leakage of personal sensitive data to external LLM providers, ensuring audit-ready corporate governance.
* **Deterministic Execution:** Pre-LLM sanitization runs in pure Python with zero external API calls or network latency (<2ms).
* **Domain Reputation Protection:** Automatic filtering of consumer mailboxes prevents accidental outreach to private citizens.

### Trade-offs
* **Maintenance of Consumer Domain Blacklist:** The list of consumer email providers requires periodic maintenance as regional webmail services emerge.
* **Conservative PII Masking:** Numeric pattern matching may occasionally flag alphanumeric serial numbers; this is mitigated by domain-specific boundary constraints.

## Consequences

* The platform satisfies corporate data governance standards required by enterprise European organizations.
* All compliance decisions are logged with structured audit flags (`CONSUMER_MAILBOX_DETECTED`, `PII_MASKED`) for complete traceability.
