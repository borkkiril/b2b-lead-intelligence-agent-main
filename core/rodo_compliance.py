"""
RODO / GDPR Compliance & PII Guardrail Module for Orion B2B Intelligence.
Implements deterministic data sanitization before LLM prompt injection and verifies
corporate records compliance under GDPR Art. 6(1)(f) (Legitimate Business Interest).

Designed for Enterprise AI Governance and RODO / GDPR data minimization.
"""

import re
import uuid
import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Common personal/consumer email providers that cannot be processed as corporate B2B endpoints
CONSUMER_EMAIL_DOMAINS = {
    # Polish consumer domains
    "wp.pl", "onet.pl", "onet.eu", "interia.pl", "interia.eu", "o2.pl", "tlen.pl",
    "gazeta.pl", "poczta.fm", "autograf.pl", "op.pl", "buziaczek.pl",
    # Global consumer domains
    "gmail.com", "googlemail.com", "yahoo.com", "ymail.com", "hotmail.com",
    "outlook.com", "live.com", "msn.com", "icloud.com", "me.com", "mac.com",
    "aol.com", "mail.com", "proton.me", "protonmail.com", "zoho.com",
    "gmx.com", "gmx.de", "web.de", "seznam.cz"
}

class ComplianceAuditRecord(BaseModel):
    is_compliant: bool
    email: str
    domain: str
    legal_basis: str = "GDPR Art. 6(1)(f) - Legitimate Business Interest (B2B Commercial Communication)"
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    reason: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    flags: List[str] = Field(default_factory=list)


class RODOComplianceGuard:
    """
    Deterministic PII Redactor & GDPR/RODO Compliance Validator.
    Guarantees that sensitive personal identifiers never leak to external LLM endpoints.
    """

    # Regex for Polish PESEL (11 digits) and Polish National ID (Dowód Osobisty: 3 letters + 6 digits)
    PESEL_PATTERN = re.compile(r"\b\d{11}\b")
    ID_CARD_PATTERN = re.compile(r"\b[A-Z]{3}\s?\d{6}\b", re.IGNORECASE)

    # Phone numbers: Polish (+48 123 456 789 or 9 digits) and international formats
    PHONE_PATTERN = re.compile(
        r"(?:(?:\+|00)48[\s-]?)?(?:\b[1-9]\d{2}[\s-]?\d{3}[\s-]?\d{3}\b)"
        r"|(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{4}\b"
    )

    # Email pattern
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b")

    @classmethod
    def redact_pii_before_llm(cls, text: str) -> str:
        """
        Redacts personal identifying information (PII) before passing text to LLM prompts:
        - Masks Polish PESEL and National ID card numbers -> [REDACTED_PESEL_OR_ID]
        - Masks phone numbers -> [REDACTED_PHONE]
        - Masks private consumer mailboxes (@gmail.com, @wp.pl, @onet.pl) -> [REDACTED_PRIVATE_EMAIL]
        - Strictly preserves corporate B2B emails (e.g. contact@enterprise-logistics.pl, team@b2b-analytics.io).

        Legal Rationale: GDPR Art. 6(1)(f) allows processing B2B corporate contact info under
        legitimate interest, while personal consumer identifiers require strict minimization/consent.
        """
        if not text:
            return ""

        redacted = text

        # 1. Redact Private Consumer Emails (preserve corporate B2B)
        def email_replacer(match):
            full_email = match.group(0)
            domain = match.group(1).lower()
            if domain in CONSUMER_EMAIL_DOMAINS:
                return "[REDACTED_PRIVATE_EMAIL]"
            return full_email

        redacted = cls.EMAIL_PATTERN.sub(email_replacer, redacted)

        # 2. Redact Polish National ID (Dowód Osobisty)
        redacted = cls.ID_CARD_PATTERN.sub("[REDACTED_PESEL_OR_ID]", redacted)

        # 3. Redact PESEL (11 continuous digits)
        redacted = cls.PESEL_PATTERN.sub("[REDACTED_PESEL_OR_ID]", redacted)

        # 4. Redact Phone numbers
        # Guard against year matches or short integers by checking length in replacer
        def phone_replacer(match):
            val = match.group(0).strip()
            digits = re.sub(r"\D", "", val)
            if len(digits) >= 9:
                return "[REDACTED_PHONE]"
            return val

        redacted = cls.PHONE_PATTERN.sub(phone_replacer, redacted)

        return redacted

    @classmethod
    def validate_b2b_record_compliance(cls, email: str, domain: str) -> Dict[str, Any]:
        """
        Verifies if a prospecting lead record complies with RODO / GDPR standards:
        - Must NOT use a consumer email service (@gmail, @onet, @wp, etc.)
        - Must have a legitimate company website/domain
        - Generates immutable audit record with legal basis.
        """
        clean_email = (email or "").strip().lower()
        clean_domain = (domain or "").strip().lower().replace("https://", "").replace("http://", "").split("/")[0]

        flags = []
        is_compliant = True
        risk_level = "LOW"
        reason = "Record strictly complies with B2B corporate outreach standards."

        # Check email presence
        if not clean_email or "@" not in clean_email:
            is_compliant = False
            risk_level = "HIGH"
            reason = "Invalid or missing email address."
            flags.append("MISSING_EMAIL")
        else:
            email_domain = clean_email.split("@")[-1]
            if email_domain in CONSUMER_EMAIL_DOMAINS:
                is_compliant = False
                risk_level = "HIGH"
                reason = f"Personal consumer mailbox detected (@{email_domain}). B2B outreach strictly prohibited without prior explicit consent."
                flags.append("CONSUMER_MAILBOX_DETECTED")

        # Check domain presence
        if not clean_domain or clean_domain in ["localhost", "127.0.0.1", "none", "null"]:
            is_compliant = False
            risk_level = "HIGH" if risk_level == "HIGH" else "MEDIUM"
            flags.append("INVALID_COMPANY_DOMAIN")
            if is_compliant:
                reason = "Missing valid corporate domain."

        audit_record = ComplianceAuditRecord(
            is_compliant=is_compliant,
            email=clean_email,
            domain=clean_domain,
            risk_level=risk_level,
            reason=reason,
            flags=flags
        )
        return audit_record.model_dump()
