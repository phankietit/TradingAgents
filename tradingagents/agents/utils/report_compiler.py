"""Resolve report quantities from immutable facts, without changing conclusions."""

import re
from decimal import Decimal, InvalidOperation

from tradingagents.agents.research_schemas import (
    CanonicalSnapshotDecision,
    CanonicalSnapshotDecisionV2,
    SnapshotReportDraft,
    SnapshotReportDraftV2,
)
from tradingagents.agents.utils.fundamental_statements import (
    fundamental_statement,
    is_fundamental_fact,
)
from tradingagents.agents.utils.quantitative_statements import (
    is_percentage_fact,
    percentage_statement,
)
from tradingagents.agents.utils.statement_anchors import non_standalone_anchors
from tradingagents.platform.analysis.research_validation import (
    PublicationValidationError,
    unsupported_financial_numbers,
)

ANCHOR = re.compile(r"\{\{(Q[A-Z]{1,5})\}\}")


def compile_report(raw, facts):
    v2 = raw.get("report_contract_version") == "2.0"
    draft = (SnapshotReportDraftV2 if v2 else SnapshotReportDraft).model_validate(raw)
    material = [*draft.investment_thesis, *draft.risks, *draft.invalidation_conditions]
    prose = "\n".join([draft.executive_summary, *[item.claim for item in material], draft.time_horizon or ""])
    if unsupported_financial_numbers(prose, ()):
        raise PublicationValidationError(["financial_number_requires_verified_reference"])
    data = draft.model_dump(mode="json")
    thesis = "\n\n".join(item.claim for item in draft.investment_thesis)
    thesis_sources = list(dict.fromkeys(str(source) for item in draft.investment_thesis for source in item.snapshot_ids))
    citations = [{"claim": thesis, "snapshot_ids": thesis_sources},
                 *[item.model_dump(mode="json") for item in (*draft.risks, *draft.invalidation_conditions)]]
    # Combining supplied paragraph citations is a lossless projection, not a
    # guessed evidence link. Unknown IDs still fail canonical validation.
    merged = {}
    for citation in citations:
        merged.setdefault(citation["claim"], []).extend(citation["snapshot_ids"])
    data.update(investment_thesis=thesis, risks=[item.claim for item in draft.risks],
                invalidation_conditions=[item.claim for item in draft.invalidation_conditions],
                evidence_claims=[{"claim": claim, "snapshot_ids": list(dict.fromkeys(ids))} for claim, ids in merged.items()])
    bindings = data.pop("quantity_bindings")
    if v2:
        summary_keys = set(ANCHOR.findall(draft.executive_summary))
        summary_sources = {str(value) for value in draft.summary_evidence.snapshot_ids}
        if any(binding["key"] in summary_keys and binding["snapshot_id"] not in summary_sources
               for binding in bindings):
            raise PublicationValidationError(["material_claim_citation_mismatch"])
    values = {}
    observations = []
    statement_keys = set()
    relation_failures = []
    fundamental_failures = []
    macro_failures = []
    social_failures = []
    for binding in bindings:
        key = binding["key"]
        source = facts.get(binding["snapshot_id"])
        value = source.resolve_fact(binding["fact_id"]) if source is not None else None
        if key in values:
            raise PublicationValidationError(["quantity_binding_duplicate"])
        if value is None:
            raise PublicationValidationError(["quantity_binding_unknown_fact"])
        try:
            number = Decimal(str(value)).quantize(Decimal(1).scaleb(-binding["decimal_places"]))
        except InvalidOperation:
            raise PublicationValidationError(["numeric_claim_not_supported"], binding_keys=(key,)) from None
        if not number.is_finite():
            raise PublicationValidationError(["numeric_claim_not_supported"])
        values[key] = format(number, "f")
        macro = binding["fact_id"].startswith("fred.")
        social = binding["fact_id"].startswith("social.")
        if not macro and not is_percentage_fact(binding["fact_id"]) and re.search(
                re.escape("{{" + key + "}}") + r"\s*(?:%|percent\b|per\s+cent\b)", prose, re.I):
            raise PublicationValidationError(["quantity_binding_unit_mismatch"], binding_keys=(key,))
        if macro or social:
            statement_keys.add(key)
            if non_standalone_anchors(prose, ["{{" + key + "}}"]):
                (social_failures if social else macro_failures).append(key)
            try:
                values[key] = source.statement(binding["fact_id"], values[key])
            except (AttributeError, ValueError):
                code = "social_statement_unsupported" if social else "macro_statement_unsupported"
                raise PublicationValidationError([code], binding_keys=(key,)) from None
        elif is_percentage_fact(binding["fact_id"]) or is_fundamental_fact(binding["fact_id"]):
            statement_keys.add(key)
            # Complete owned statements prevent changing a percentage's
            # denominator or an accounting fact's metric, period or units.
            fundamental = is_fundamental_fact(binding["fact_id"])
            if non_standalone_anchors(prose, ["{{" + key + "}}"]):
                (fundamental_failures if fundamental else relation_failures).append(key)
            try:
                renderer = fundamental_statement if fundamental else percentage_statement
                values[key] = renderer(binding["fact_id"], values[key])
            except ValueError:
                code = "fundamental_statement_unsupported" if fundamental else "percentage_statement_unsupported"
                raise PublicationValidationError([code], binding_keys=(key,)) from None
        observations.append(
            {name: binding[name] for name in ("snapshot_id", "fact_id", "decimal_places")}
            | {"value": float(number)}
        )
    if relation_failures:
        raise PublicationValidationError(["percentage_statement_requires_standalone_anchor"], binding_keys=relation_failures)
    if fundamental_failures:
        raise PublicationValidationError(["fundamental_statement_requires_standalone_anchor"], binding_keys=fundamental_failures)
    if macro_failures:
        raise PublicationValidationError(["macro_statement_requires_standalone_anchor"], binding_keys=macro_failures)
    if social_failures:
        raise PublicationValidationError(["social_statement_requires_standalone_anchor"], binding_keys=social_failures)
    used = set()

    def render(value):
        if isinstance(value, str):

            def replace(match):
                key = match.group(1)
                if key not in values:
                    raise PublicationValidationError(["quantity_binding_missing"])
                used.add(key)
                if key in statement_keys and match.string[match.end():].startswith("."):
                    return values[key].removesuffix(".")
                return values[key]

            result = ANCHOR.sub(replace, value)
            if "{{" in result or "}}" in result:
                raise PublicationValidationError(["quantity_anchor_malformed"])
            return result
        if isinstance(value, list):
            return [render(item) for item in value]
        if isinstance(value, dict):
            return {key: render(item) for key, item in value.items()}
        return value

    data = render(data)
    if used != set(values):
        raise PublicationValidationError(["quantity_binding_unused"])
    data["observed_numbers"] = observations
    return (CanonicalSnapshotDecisionV2 if v2 else CanonicalSnapshotDecision).model_validate(data)


def compile_report_v2(raw, facts):
    """Strict new-generation entry: removing both V2 fields cannot downgrade.

    The legacy compiler stays available for separately identified historical
    inputs, never new-output fallback.
    """
    SnapshotReportDraftV2.model_validate(raw)
    return compile_report(raw, facts)


BINDING_INSTRUCTIONS = """
QUANTITY CONTRACT: Write ALL monetary amounts, percentages and calculated quantities as
placeholders {{QA}}, {{QB}}, etc.; create quantity_bindings with key QA/QB, exact
snapshot_id, verified fact_id and decimal_places. Do NOT put values in bindings.
PERCENTAGE STATEMENTS: Each percentage binding MUST occupy a complete standalone
sentence: '{{QA}}.' with NO surrounding percentage sign, subject, comparison,
direction, unit or other words in that sentence. The application renders the
entire verified relationship in English and Vietnamese, choosing the subject,
reference and denominator ONLY from the fact ID. This includes calendar returns,
indicator percentages, drawdown and calc.pct_change/abs_pct_change. Retain ALL
material comparisons by selecting the correct fact IDs, not by dropping them.
Keep the associated financial interpretation, opposing case and uncertainty in
separate sentences. Do not negate, quote as false or contradict the observation.
SEC ACCOUNTING STATEMENTS: Every sec.* binding MUST also occupy a complete
standalone sentence '{{QA}}.' without surrounding currency, scale, metric,
period or other prose. The application renders the exact reported metric,
annual/quarterly period and USD millions or USD per-share unit from the fact ID,
in both languages. Do not label a million-unit fact as billions or earnings
per share, or an annual balance as current-quarter revenue. Keep accounting
interpretations and opposing evidence in separate sentences. A
fundamental_statement_requires_standalone_anchor failure means move the SEC
anchor into its own complete sentence; do not remove the underlying evidence.
Other non-percentage price/volume bindings remain inline numeric anchors.
SOCIAL SAMPLE COUNTS: Every social.* binding MUST occupy a complete standalone
sentence '{{QA}}.' with no surrounding money, percentage, label or interpretation.
The application owns its vendor, sample-count unit and user-label limitations
in English and Vietnamese. Counts are not price, market probability or complete
market coverage; unlabeled does not mean neutral. Keep the financial interpretation
and opposing evidence in separate sentences; do not omit them to pass a check.
FRED MACRO STATEMENTS: Every fred.* binding MUST occupy a complete standalone
sentence '{{QA}}.' without surrounding units, series, observation period,
vintage or comparison words. The application owns the full native-unit/period/
vintage statement in both languages. Native levels are NOT automatically
inflation or growth rates. difference uses native units (percentage points for
Percent); pct_change uses the explicit reference observation as denominator,
not a percentage-point difference or an asset return. Use exact paginated
FRED fact IDs; missing operands are unavailable, never zero or an estimate.
A macro_statement_requires_standalone_anchor failure means move the anchor
into its own sentence, preserving its interpretation/opposing evidence nearby.
Keys must match Q[A-Z]{1,5}: uppercase letters only, e.g. QA, QZ, QAA, QAB.
For close C and reference R, price premium over R is (C/R - 1)*100,
but a move from C to R is (R/C - 1)*100. Never reuse the former for the latter.
Exact ID meanings:
- indicator.NAME.latest_close_vs_indicator_pct: signed (C/R - 1)*100.
- indicator.NAME.latest_close_distance_magnitude_pct: absolute (C/R - 1)*100.
- indicator.NAME.distance_from_latest_close_pct: signed (R/C - 1)*100.
- calc.abs_pct_change(indicator.NAME,latest.close): absolute (R/C - 1)*100.
- observed_window.latest_close_vs_high_pct: signed change relative to window high.
- observed_window.drawdown_magnitude_pct: positive magnitude below window high.
For a magnitude below a level, use a positive magnitude, not a signed negative
return followed by 'below'. A percentage_statement_requires_standalone_anchor
failure means move the percentage anchor into its own complete sentence without
words or %. Preserve the interpretation in adjacent prose. Do not change the
underlying market values or remove inconvenient evidence.
Every binding must appear in the prose, and every placeholder must have exactly
one binding. Do not copy the entire catalog into bindings. An unused-binding
failure means remove only an unreferenced binding, NOT its supported arguments
or opposing evidence. An unknown-fact failure means use an exact supplied ID,
never invent an alias. A missing-binding failure means bind the actual referenced
quantity. A malformed-anchor failure means fix placeholder syntax only.
Example prose: 'The close was ${{QA}}. {{QB}}. Momentum remains positive.' Bind QA
to latest.close and QB to return.30_calendar_days.pct from the supplied snapshot.
Keep currency outside INLINE MARKET-PRICE placeholders only. SEC placeholders
own their entire accounting sentence; never attach currency, scale or period.
NEVER append % to a percentage placeholder; its complete sentence owns the unit
and relationship. Reuse each binding consistently
in source-linked claim objects. Leave observed_numbers empty and price_target null. Application
code resolves all quantities; do not calculate or copy numeric observations into
prose, INCLUDING approximate or conditional quantities. Do not replace a bound
percentage with a rough rounded percentage. Indicator names (SMA 50), periods, dates and explicitly conditional indicator
thresholds may retain digits. Use verified calc.* or window.* IDs for derived facts.
Never invent a fact ID, omit opposing evidence, or turn an unsupported calculation
into an observed fact. Use evidence-linked objects for every thesis paragraph,
risk and invalidation: each object has claim (prose with placeholders) and
snapshot_ids. Leave top-level evidence_claims empty; application code compiles
the exact references, without asking you to duplicate prose.
"""
