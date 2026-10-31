# Engineering & AI Governance Guidelines: Orion Platform

> **Wdrażanie dobrych praktyk wykorzystania AI w organizacji / AI Agent Engineering Standard**  
> *Targeted for Enterprise AI Governance and Production AI Agent Operations.*

---

## 1. AI Prompt Engineering & Workflow Standards

1. **Deterministic Structured Outputs:**
   * All LLM responses must be parsed into strongly typed **Pydantic v2** schemas (`BaseModel`). Raw or unstructured JSON strings must never be passed directly to downstream business logic or databases.
   * Model temperature for analytical workflows, data normalization, and compliance checks must be fixed to `temperature = 0.0` or `0.1` to eliminate non-deterministic hallucinations.

2. **Decoupled Evaluator-Creator Pipeline (Two-Stage QA):**
   * Never evaluate and generate copy or code within a single monolithic prompt.
   * **Stage 1 (Creator/Synthesizer):** Generates structured drafts or blueprints.
   * **Stage 2 (Adversarial Evaluator):** Evaluates outputs against objective binary quality gates (e.g. 5 Content & Deliverability QA Gates in `outreach-simulator`) on low-latency models (Gemini Flash).
   * **Stage 3 (Surgical Revisor):** Deep reasoning models (Claude Sonnet / Gemini Pro) rewrite *only* the specific identified bottleneck.

3. **Prompt Versioning & Modularity:**
   * Prompts live in version-controlled markdown specifications (`.agent/skills/`), decoupled from the Python execution core.
   * Prompt changes must include before/after regression benchmarks.

---

## 2. RODO / GDPR & PII Data Protection Guardrails

1. **Pre-LLM Sanitization (Zero Leak Standard):**
   * Before any textual payload or document is transmitted to an external LLM API (OpenAI, Gemini, Anthropic), it must pass through `RODOComplianceGuard.redact_pii_before_llm()`.
   * **Prohibited Data in LLM Prompts:**
     - Polish PESEL numbers (11 digits) -> masked to `[REDACTED_PESEL_OR_ID]`.
     - Polish National ID cards (Dowód Osobisty: 3 letters + 6 digits) -> masked to `[REDACTED_PESEL_OR_ID]`.
     - Personal mobile/landline telephone numbers -> masked to `[REDACTED_PHONE]`.
     - Private/consumer email mailboxes (`@gmail.com`, `@wp.pl`, `@onet.pl`, `@interia.pl`, etc.) -> masked to `[REDACTED_PRIVATE_EMAIL]`.

2. **B2B Legal Ground (GDPR Art. 6(1)(f)):**
   * Only legitimate business entities and corporate decision-maker email addresses associated with active corporate domains are processed under the legal basis of *Legitimate Business Interest* (B2B commercial communication).
   * Any lead record failing `validate_b2b_record_compliance()` is blocked from outbound pipelines with an explicit audit log.

---

## 3. Data Integrity & Pydantic v2 Typing Standards

1. **Type Safety & Schema Validation:**
   * Every business model (Lead, AuditRecord, HealthReport, Milestone) must inherit from `pydantic.BaseModel`.
   * Use `Field(..., description=...)` with default factories to prevent mutable default bugs.

2. **Database State Immutability (ACID):**
   * All mutations to the SQLite persistence layer (`data/leads.db`) must run through explicit parameterized transactions.
   * Update operations on draft records must strictly enforce `WHERE status = 'DRAFT'` (or localized display status) to prevent overwriting active or in-flight communication records.

---

## 4. Multi-Server Linux/SSH & Production Operations

1. **Automated Pre-Flight Gate:**
   * No deployment may proceed to production servers without passing the local test suite:
     ```bash
     python -m unittest discover tests -v
     ```
   * Total test execution time must remain **strictly below 1.0 second** to ensure instant feedback in CI/CD.

2. **SSH Cluster Deployment with Automated Rollback:**
   * Multi-server deployments are automated via `deploy/ssh_multi_deploy.sh`.
   * Each node automatically archives the current state (`backups/backup_*.tar.gz`) before pulling new Git revisions.
   * If `core/health_monitor.py` detects database latency exceeding 45ms or SQLite integrity failures, an automated `git reset --hard` rollback is immediately triggered via bash `trap ... ERR`.

3. **Containerization & CIS Docker Standards:**
   * Production Docker containers (`Dockerfile`) must run as an unprivileged non-root user (`orionuser:10001`).
   * Containers must define an active `HEALTHCHECK` command executing `core/health_monitor.py`.

---

## 5. Definition of Done (DoD) for AI Features

A feature or AI skill is considered production-ready when:
1. It is documented with an Architecture Decision Record in `docs/adr/` (Nygard format).
2. It has unit tests in `tests/test_system.py` with 100% pass rate in <1s.
3. It complies with `RODOComplianceGuard` sanitization rules.
4. It includes health monitoring hooks for telemetry alerting.
