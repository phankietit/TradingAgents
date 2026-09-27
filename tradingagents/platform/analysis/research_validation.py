"""Conservative publication checks, separate from source and portfolio health.

These checks validate explicit quantitative references and known authority
violations, not the truth of every qualitative inference. Human review remains
required; a valid citation alone is not proof that a thesis follows from it.
"""

import re
from collections import Counter
from contextlib import suppress
from decimal import Decimal, InvalidOperation

UUID_PATTERN = re.compile(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b", re.I)
NUMBER_PATTERN = re.compile(r"(?<![\w])[-+]?\d+(?:,\d{3})*(?:\.\d+)?%?")

PUBLICATION_CODES = frozenset({"numeric_claim_not_supported", "financial_number_requires_verified_reference",
    "research_authority_requires_review", "material_claim_citation_mismatch", "unknown_snapshot_reference",
    "translation_anchor_mismatch", "translation_numeric_token_added", "translation_reserved_anchor"})


class PublicationValidationError(ValueError):
    def __init__(self, issues):
        self.issues = tuple(sorted(set(issues) & PUBLICATION_CODES))
        super().__init__("research publication checks failed")


def validate_canonical_report(decision, fact_sources, snapshot_ids):
    """Reuse publication gates before bounded PM repair; never rewrite a claim."""
    catalog = {key: source.fact_catalog() for key, source in fact_sources.items()}
    for claim in decision.observed_numbers:
        source = fact_sources.get(str(claim.snapshot_id))
        if source is not None:
            with suppress(ValueError, KeyError, IndexError):
                catalog[str(claim.snapshot_id)][claim.fact_id] = source.resolve_fact(claim.fact_id)
    text = "\n".join([decision.executive_summary, decision.investment_thesis,
        *decision.risks, *decision.invalidation_conditions, decision.time_horizon or ""])
    issues = scope_issues(text) + validate_numeric_claims(decision.observed_numbers, catalog)
    if unsupported_financial_numbers(text, decision.observed_numbers):
        issues.append("financial_number_requires_verified_reference")
    material = {decision.investment_thesis, *decision.risks, *decision.invalidation_conditions}
    claims = [item.claim for item in decision.evidence_claims]
    if set(claims) != material or len(claims) != len(material):
        issues.append("material_claim_citation_mismatch")
    if any(str(source) not in snapshot_ids for item in decision.evidence_claims for source in item.snapshot_ids):
        issues.append("unknown_snapshot_reference")
    if issues:
        raise PublicationValidationError(issues)


def number_tokens(text: str) -> Counter:
    text = UUID_PATTERN.sub("", text).replace("−", "-")
    return Counter(token.replace(",", "").lstrip("+") for token in NUMBER_PATTERN.findall(text))


def validate_numeric_claims(claims, catalog: dict[str, dict]) -> list[str]:
    issues = []
    for claim in claims:
        facts = catalog.get(str(claim.snapshot_id), {})
        expected = facts.get(claim.fact_id)
        try:
            actual = Decimal(str(claim.value))
            # Decimal rounding only, never percent-vs-ratio auto-conversion.
            quantum = Decimal(1).scaleb(-claim.decimal_places)
            valid = expected is not None and actual == actual.quantize(quantum) and actual == Decimal(str(expected)).quantize(quantum)
        except (InvalidOperation, ValueError, TypeError):
            valid = False
        if not valid:
            issues.append("numeric_claim_not_supported")
    return list(dict.fromkeys(issues))


def unsupported_financial_numbers(text: str, claims) -> bool:
    """Require explicit references for money/percent observations in final prose.

    Other numeric semantics and qualitative entailment still require review.
    Conditional price assumptions lacking source support deliberately withhold
    readiness rather than being mislabeled as verified market facts.
    """
    amounts = re.findall(r"(?:\$|USD\s*)\s*([-+−]?\d+(?:,\d{3})*(?:\.\d+)?)|([-+−]?\d+(?:,\d{3})*(?:\.\d+)?)\s*%", text)
    supported = {Decimal(str(claim.value)) for claim in claims}
    return any(Decimal((money or percent).replace(",", "").replace("−", "-")) not in supported
               for money, percent in amounts)


SCOPE_PATTERNS = (
    r"\b(?:trim|allocate|size|sell|buy|reduce|increase)\b[^.\n]{0,55}\d+(?:[–-]\d+)?\s*%",
    r"\b(?:buy|sell|use|execute)\b[^.\n]{0,50}\b(?:put spread|call spread|options hedge|leveraged|short position)\b",
    r"\b(?:phân bổ|cắt giảm|giảm tỷ trọng|tăng tỷ trọng|mua|bán)\b[^.\n]{0,45}\d+(?:[–-]\d+)?\s*%",
)


def scope_issues(text: str) -> list[str]:
    # Conservative review flag, not a substitute for schema/risk/approval gates.
    return ["research_authority_requires_review"] if any(re.search(pattern, text, re.I) for pattern in SCOPE_PATTERNS) else []
