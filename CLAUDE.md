# Engineering & AI Governance Guidelines: B2B Lead Intelligence Agent

> **AI Agent Engineering Standards & Governance Guidelines**  
> *Targeted for Antigravity 2.0 Agentic Workflows, Gemini Inference, and Enterprise AI Quality Assurance.*

---

## 1. AI Prompt Engineering & Workflow Decomposition

1. **Deterministic Structured Outputs:**
   * All LLM responses must be parsed into strongly typed **Pydantic v2** schemas (`BaseModel`). Raw or unstructured JSON strings must never be passed directly to downstream business logic or database layers.
   * Model temperature for analytical workflows, data normalization, and compliance checks must be fixed to `temperature = 0.0` or `0.1` to eliminate non-deterministic hallucinations.

2. **Two-Stage Multi-Model QA Architecture:**
   * Never evaluate and generate copy or architecture specs within a single monolithic prompt.
   * **Stage 1 (Creator / Discovery):** Research target domain and generate initial operational hypotheses (`lead-enricher`).
   * **Stage 2 (Adversarial Evaluator):** Stress-test draft communications against 5 objective Content & Deliverability QA Gates on high-throughput models (**Gemini 3.8 Flash** via `outreach-simulator`).
   * **Stage 3 (Surgical Revisor):** Deep reasoning models rewrite *only* the specific identified bottleneck on unsent drafts (`outreach-revisor`).

3. **Prompt Versioning & Modularity:**
   * Prompts live in version-controlled markdown specifications (`.agent/skills/`), decoupled from the application execution core.
   * Prompt updates must include clear before/after comparison criteria and test assertions.

---

## 2. RODO / GDPR & PII Data Minimization Guardrails

1. **Pre-LLM Sanitization (Zero Leak Standard):**
   * Before any textual payload or document is transmitted to an external LLM API (Gemini, OpenAI), it must pass through `RODOComplianceGuard.redact_pii_before_llm()`.
   * **Prohibited Data in LLM Prompts:**
     - Polish PESEL numbers (11 digits) -> masked to `[REDACTED_PESEL_OR_ID]`.
     - Polish National ID cards (Dowód Osobisty: 3 letters + 6 digits) -> masked to `[REDACTED_PESEL_OR_ID]`.
     - Personal mobile/landline telephone numbers -> masked to `[REDACTED_PHONE]`.
     - Private/consumer email mailboxes (`@gmail.com`, `@wp.pl`, `@onet.pl`, etc.) -> masked to `[REDACTED_PRIVATE_EMAIL]`.

2. **B2B Legal Ground (GDPR Art. 6(1)(f)):**
   * Only legitimate business entities and corporate decision-maker email addresses associated with active corporate domains are processed under the legal basis of *Legitimate Business Interest* (B2B commercial communication).
   * Any lead record failing `validate_b2b_record_compliance()` is blocked from outbound pipelines with an explicit audit log.

---

## 3. Data Integrity & Pydantic v2 Typing Standards

1. **Type Safety & Schema Validation:**
   * Every business entity (LeadRecord, ComplianceResult, Blueprint) must inherit from `pydantic.BaseModel`.
   * Use `Field(..., description=...)` with default factories to prevent mutable default bugs.

2. **Database State Immutability (ACID):**
   * All mutations to the SQLite persistence layer (`data/leads.db`) must run through explicit parameterized transactions.
   * Update operations on draft records must strictly enforce `WHERE status IN ('Draft', 'DRAFT', 'Не відправлено')` to prevent overwriting active or in-flight communication records.

---

## 4. UI Layer & AI-Assisted Prototyping

1. **AI-Assisted Prototyping Note:**
   * The local dashboard (Flet/SQLite) and interactive HTML demo were prototyped using AI-assisted development (Vibe-coding in Antigravity) to visualize agent outputs and database state.
   * The UI layer remains strictly decoupled from agent reasoning: agents interact with the system via SQLite data contracts and skill specifications.

---

## 5. Definition of Done (DoD) for AI Features

A feature or AI skill is considered complete when:
1. It is documented with an Architecture Decision Record in `docs/adr/` (Nygard format).
2. It has unit tests in `tests/test_system.py` with 100% pass rate in <1s.
3. It complies with `RODOComplianceGuard` data minimization rules.
4. Output schemas are strictly validated via Pydantic v2 models.
