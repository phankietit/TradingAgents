"""Known relation-loss guards, not general semantic entailment or translation QA.

Patterns cover financial action/epistemic qualifiers in complete source blocks.
They never rewrite a translation or claim that a passing block is semantically
correct. Unknown paraphrases may require review; independent editorial/live
acceptance remains necessary. No model call or decision authority lives here.
"""

import re
import unicodedata
from collections import Counter

from tradingagents.platform.analysis.research_validation import PublicationValidationError


def _text(value):
    return unicodedata.normalize("NFC", value).casefold()


# Bilingual recognition also preserves meaning in application-owned English
# statements. It is not a language-detection or English-only fallback policy.
ACTION = r"\b(?:buy(?:ing)?|purchas\w*|sell(?:ing)?|reduc\w*|exposure|entr(?:y|ies)|positions?|mua|bán|giảm|tỷ trọng|vị thế)\b"
EPISTEMIC = r"\b(?:evidence|confirm\w*|establish\w*|verified|bằng chứng|xác nhận|xác lập|kiểm chứng)\b"
OUTLOOK = r"\b(?:improv\w*|ris\w*|increas\w*|declin\w*|fall\w*|case|scenario|revers\w*|trend|support|price|momentum|cải thiện|tăng|giảm|kịch bản|đảo chiều|xu hướng|hỗ trợ|giá|động lượng)\b"

RELATIONS = (
    ("aggressive", ACTION, r"\baggressiv\w*\b", r"\baggressiv\w*\b|mạnh tay|mạnh mẽ|quyết liệt"),
    ("gradual", ACTION, r"\bgradual\w*\b", r"\bgradual\w*\b|\bdần\b|từng bước|từ từ"),
    ("exclusive", ACTION, r"\bonly\b", r"\bonly\b|\bchỉ\b|duy nhất"),
    ("until", f"{ACTION}|{OUTLOOK}", r"\buntil\b", r"\buntil\b|cho đến khi|đến khi"),
    ("after", f"{ACTION}|{OUTLOOK}", r"\bafter\b", r"\bafter\b|\bsau khi\b|\bsau lúc\b"),
    ("conditional", f"{ACTION}|{OUTLOOK}", r"\bif\b", r"\bif\b|\bnếu\b|\bkhi\b|trong trường hợp"),
    ("uncertain", f"{ACTION}|{EPISTEMIC}|{OUTLOOK}", r"\b(?:may|might|could|possible|possibly)\b",
     r"\b(?:may|might|could|possible|possibly)\b|có thể|khả năng|có khả năng|không thể"),
    ("unconfirmed", EPISTEMIC, r"\b(?:not|unconfirmed|unverified)\b",
     r"\b(?:not|unconfirmed|unverified)\b|\bchưa\b|\bkhông\b|thiếu cơ sở|chưa có cơ sở"),
    ("opposing_case_retained", r"\b(?:bearish|bullish)\b.*\b(?:case|scenario)\b|kịch bản.*(?:tăng|giảm) giá",
     r"\bremain\w*\b", r"\bremain\w*\b|\bvẫn\b|\bcòn\b"),
)


def validate_translation_qualifiers(english, vietnamese):
    """Withhold observed qualifier losses, using the existing bounded repair.

    Count requirements by source sentences so one retained marker cannot cover
    two separate source conditions. This is not cross-language causal alignment;
    changed actors/objects and unsupported paraphrases still need semantic review.
    """
    original, translated = _text(english), _text(vietnamese)
    # Decimal points are not sentence boundaries. Keep quantified conditions
    # together rather than accidentally separating their subject from a marker.
    source_sentences = re.split(r"[!?;]|\.(?!\d)", original)
    target_sentences = re.split(r"[!?;]|\.(?!\d)", translated)
    required = Counter()
    for sentence in source_sentences:
        for name, domain, source_marker, _ in RELATIONS:
            # Month names are not modal verbs. Mask only explicit calendar
            # contexts, not capitalization (MAY can legitimately mean may).
            marker_source = sentence
            if name == "uncertain":
                marker_source = re.sub(r"\b(in|during|since|before|after|until|through|by|of)\s+may\b",
                    r"\1 calendar_month", marker_source)
                marker_source = re.sub(r"\bmay(?=\s+\d)|(?<=\d)\s+may\b", " calendar_month", marker_source)
            if re.search(domain, sentence) and re.search(source_marker, marker_source):
                required[name] += 1
    for name, domain, _, target_marker in RELATIONS:
        present = sum(bool(re.search(domain, sentence) and re.search(target_marker, sentence))
                      for sentence in target_sentences)
        if required[name] and present < required[name]:
            raise PublicationValidationError(["translation_qualifier_requires_review"])


EXTERNAL_MOTIVE = re.compile(r"\b(?:tax[- ]loss (?:selling|harvesting)|profit[- ]taking|"
    r"institutional (?:buying|selling|flows?)|retail flows?|etf (?:inflows?|outflows?)|"
    r"buybacks?|liquidations?)\b", re.I)
CAUSE = re.compile(r"\b(?:explain\w*|caus\w*|driven by|due to|because of|attribut\w* to|fuel\w* by)\b", re.I)
HYPOTHESIS = re.compile(r"\b(?:may|might|could|possibly|hypothes\w*|unverified|unconfirmed)\b", re.I)
UNSUPPORTED_DISCLOSURE = re.compile(r"\b(?:not (?:established|confirmed|verified|supported)|"
    r"(?:no|insufficient|missing) (?:evidence|support))\b", re.I)


def validate_price_only_attributions(decision, sources):
    """Prices cannot prove known external motives/flows as factual causes.

    A conditional unverified inference remains research, not an observation.
    Coverage is claim-local: a separate nonprice source elsewhere in the run
    cannot substantiate a claim citing only prices. Actual mixed citations still
    require semantic review; this does not authenticate a news/source statement.
    """
    if not sources:
        return
    price_ids = {str(source["snapshot_id"]) for source in sources
                 if source["provenance"]["dataset"] == "ohlcv.daily"}
    fields = []
    if all(source["provenance"]["dataset"] == "ohlcv.daily" for source in sources):
        fields.extend([decision.executive_summary, decision.investment_thesis,
                       *decision.risks, *decision.invalidation_conditions])
    for claim in decision.evidence_claims:
        cited = {str(snapshot_id) for snapshot_id in claim.snapshot_ids}
        if cited and cited <= price_ids:
            fields.append(claim.claim)
    for field in fields:
        for sentence in re.split(r"[.!?;]\s*", field):
            if (EXTERNAL_MOTIVE.search(sentence) and CAUSE.search(sentence)
                    and not HYPOTHESIS.search(sentence) and not UNSUPPORTED_DISCLOSURE.search(sentence)):
                raise PublicationValidationError(["external_cause_requires_nonprice_evidence"])
