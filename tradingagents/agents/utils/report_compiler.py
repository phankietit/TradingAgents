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
    prose = "\n".join(
        [
            draft.executive_summary,
            draft.investment_thesis,
            *draft.risks,
            *draft.invalidation_conditions,
            draft.time_horizon or "",
        ]
    )
    if unsupported_financial_numbers(prose, ()):
        raise PublicationValidationError(["financial_number_requires_verified_reference"])
    data = draft.model_dump(mode="json")
    bindings = data.pop("quantity_bindings")
    values = {}
    observations = []
    for binding in bindings:
        key = binding["key"]
        source = facts.get(binding["snapshot_id"])
        value = source.resolve_fact(binding["fact_id"]) if source is not None else None
        if key in values or value is None:
            raise PublicationValidationError(["numeric_claim_not_supported"])
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
                    raise PublicationValidationError(["numeric_claim_not_supported"])
                used.add(key)
                return values[key]

            result = ANCHOR.sub(replace, value)
            if "{{" in result or "}}" in result:
                raise PublicationValidationError(["numeric_claim_not_supported"])
            return result
        if isinstance(value, list):
            return [render(item) for item in value]
        if isinstance(value, dict):
            return {key: render(item) for key, item in value.items()}
        return value

    data = render(data)
    if used != set(values):
        raise PublicationValidationError(["numeric_claim_not_supported"])
    data["observed_numbers"] = observations
    return CanonicalSnapshotDecision.model_validate(data)


BINDING_INSTRUCTIONS = """
QUANTITY CONTRACT: Write observed prices, percentages and calculated quantities as
placeholders {{QA}}, {{QB}}, etc.; create quantity_bindings with key QA/QB, exact
snapshot_id, verified fact_id and decimal_places. Do NOT put values in bindings.
Example prose: 'The close was ${{QA}}.' Bind QA to latest.close from the supplied
snapshot. Keep currency/% outside the placeholder. Reuse each binding consistently
in evidence_claims. Leave observed_numbers empty and price_target null. Application
code resolves all quantities; do not calculate or copy numeric observations into
prose. Indicator names (SMA 50), periods, dates and explicitly conditional indicator
thresholds may retain digits. Use verified calc.* or window.* IDs for derived facts.
Never invent a fact ID, omit opposing evidence, or turn an unsupported calculation
into an observed fact. Evidence claims must exactly match the unrendered thesis,
risks and invalidation strings, including placeholders.
"""
