"""Resolve report quantities from immutable facts, without changing conclusions."""

import re
from decimal import Decimal

from tradingagents.agents.research_schemas import CanonicalSnapshotDecision, SnapshotReportDraft
from tradingagents.platform.analysis.research_validation import (
    PublicationValidationError,
    unsupported_financial_numbers,
)

ANCHOR = re.compile(r"\{\{(Q[A-Z]{1,5})\}\}")


def compile_report(raw, facts):
    draft = SnapshotReportDraft.model_validate(raw)
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
    values = {}
    observations = []
    for binding in bindings:
        key = binding["key"]
        source = facts.get(binding["snapshot_id"])
        value = source.resolve_fact(binding["fact_id"]) if source is not None else None
        if key in values:
            raise PublicationValidationError(["quantity_binding_duplicate"])
        if value is None:
            raise PublicationValidationError(["quantity_binding_unknown_fact"])
        number = Decimal(str(value)).quantize(Decimal(1).scaleb(-binding["decimal_places"]))
        if not number.is_finite():
            raise PublicationValidationError(["numeric_claim_not_supported"])
        values[key] = format(number, "f")
        observations.append(
            {name: binding[name] for name in ("snapshot_id", "fact_id", "decimal_places")}
            | {"value": float(number)}
        )
    used = set()

    def render(value):
        if isinstance(value, str):

            def replace(match):
                key = match.group(1)
                if key not in values:
                    raise PublicationValidationError(["quantity_binding_missing"])
                used.add(key)
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
    return CanonicalSnapshotDecision.model_validate(data)


BINDING_INSTRUCTIONS = """
QUANTITY CONTRACT: Write ALL monetary amounts, percentages and calculated quantities as
placeholders {{QA}}, {{QB}}, etc.; create quantity_bindings with key QA/QB, exact
snapshot_id, verified fact_id and decimal_places. Do NOT put values in bindings.
Keys must match Q[A-Z]{1,5}: uppercase letters only, e.g. QA, QZ, QAA, QAB.
Every binding must appear in the prose, and every placeholder must have exactly
one binding. Do not copy the entire catalog into bindings. An unused-binding
failure means remove only an unreferenced binding, NOT its supported arguments
or opposing evidence. An unknown-fact failure means use an exact supplied ID,
never invent an alias. A missing-binding failure means bind the actual referenced
quantity. A malformed-anchor failure means fix placeholder syntax only.
Example prose: 'The close was ${{QA}}.' Bind QA to latest.close from the supplied
snapshot. Keep currency/% outside the placeholder. Reuse each binding consistently
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
