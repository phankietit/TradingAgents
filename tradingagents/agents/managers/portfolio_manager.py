"""Portfolio Manager: synthesises the risk-analyst debate into the final decision.

Uses LangChain's ``with_structured_output`` so the LLM produces a typed
``PortfolioDecision`` directly, in a single call.  The result is rendered
back to markdown for storage in ``final_trade_decision`` so memory log,
CLI display, and saved reports continue to consume the same shape they do
today.  When a provider does not expose structured output, the agent falls
back gracefully to free-text generation.
"""

from __future__ import annotations

from tradingagents.agents.schemas import PortfolioDecision, render_pm_decision
from tradingagents.agents.utils.agent_utils import (
    get_instrument_context_from_state,
    get_language_instruction,
    get_portfolio_context_from_state,
)
from tradingagents.agents.utils.structured import (
    NO_EXTERNAL_TOOLS,
    bind_structured,
    invoke_structured_or_freetext,
)


def create_portfolio_manager(llm, *, research_only=False, snapshot_reports=None):
    from tradingagents.agents.research_schemas import CanonicalSnapshotDecision

    schema = CanonicalSnapshotDecision if research_only else PortfolioDecision
    structured_llm = bind_structured(llm, schema, "Portfolio Manager")
    fact_sources, snapshot_ids = {}, set()
    if snapshot_reports is not None:
        import json

        from tradingagents.platform.analysis.market_facts import SnapshotMarketFacts

        for report in snapshot_reports.values():
            for source in json.loads(report):
                snapshot_ids.add(source["snapshot_id"])
                if source["provenance"]["dataset"] == "ohlcv.daily":
                    fact_sources[source["snapshot_id"]] = SnapshotMarketFacts(source)

    def portfolio_manager_node(state) -> dict:
        instrument_context = get_instrument_context_from_state(state)
        portfolio_context = get_portfolio_context_from_state(state)

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        research_plan = state["investment_plan"]
        trader_plan = state["trader_investment_plan"]

        past_context = state.get("past_context", "")
        lessons_line = (
            f"- Lessons from prior decisions and outcomes:\n{past_context}\n"
            if past_context
            else ""
        )

        prompt = f"""As the Portfolio Manager, synthesize the risk analysts' debate and deliver the final trading decision.

{instrument_context}

{portfolio_context}

---

**Rating Scale** (use exactly one):
- **Buy**: Strong conviction to enter or add to position
- **Overweight**: Favorable outlook, gradually increase exposure
- **Hold**: Maintain current position, no action needed
- **Underweight**: Reduce exposure, take partial profits
- **Sell**: Exit position or avoid entry

**Context:**
- Research Manager's investment plan: **{research_plan}**
- Trader's transaction proposal: **{trader_plan}**
{lessons_line}
**Risk Analysts Debate History:**
{history}

---

Ground every conclusion in specific evidence from the analysts. The risk debate always contains conflicting stances; deciding which is stronger is the job, so conflict alone is not a reason to Hold. Commit to the stronger case, sized by how decisively it wins. Choose Hold only when the evidence is still balanced after that weighing, or too thin to support a call; do not force a direction to appear decisive. Weigh the analysts on their merits, independent of speaking order.

## Output

Write these sections, in this order, starting with the rating on its own line:

- **Rating**: exactly one of Buy / Overweight / Hold / Underweight / Sell
- **Executive Summary**: the call and how to act on it
- **Investment Thesis**: the evidence that decided it, and what would change it

{NO_EXTERNAL_TOOLS}{get_language_instruction()}"""

        structured_decision = None
        diagnostics = list(state.get("structured_diagnostics", []))
        if research_only:
            # The legacy bilingual suffix asks for both languages in every
            # field. Snapshot reports have separate locales; do not contradict
            # that schema with the legacy instruction.
            prompt = prompt.replace(get_language_instruction(), "")
            prompt = prompt.replace("final trading decision", "final research assessment")
            for old, new in {
                "Strong conviction to enter or add to position": "Strong positive research outlook",
                "Favorable outlook, gradually increase exposure": "Moderately positive research outlook",
                "Maintain current position, no action needed": "Balanced or insufficient research evidence",
                "Reduce exposure, take partial profits": "Moderately negative research outlook",
                "Exit position or avoid entry": "Strong negative research outlook",
                "the call and how to act on it": "outlook, supporting evidence, uncertainty and horizon",
                "Trader's transaction proposal": "Trader's research scenario",
            }.items():
                prompt = prompt.replace(old, new)
            prompt = prompt.replace("sized by how decisively it wins", "qualified by the evidence strength")
            prompt += ("\nResearch-only output: include required confidence, at least one risk, "
                       "and at least one invalidation condition. For investment_thesis and every "
                       "risk and invalidation, include an evidence_claim with exactly matching "
                       "claim text and only supplied snapshot IDs. The evidence_claims array must "
                       "contain EXACTLY the investment_thesis string, each risks string and each "
                       "invalidation_conditions string, one entry per unique string; no paraphrases "
                       "or extra entries. Hypothetical conditions must "
                       "be labelled conditional, not observed. No sizing or execution instructions.")
            prompt += ("\nUse observed_numbers to reference every observed numeric claim using "
                       "the supplied verified fact_catalog IDs and exact units. Preserve the fact_catalog "
                       "passed by analysts; do not invent IDs. Write canonical structured fields in English "
                       "only. Set localized_report=null; a separate presentation stage handles translation. "
                       "Include the strongest opposing case and coverage limitations within investment_thesis. "
                       "Use concise paragraphs with descriptive headings, not numbered headings. "
                       "Round monetary/percentage observations to 2 decimals in prose and observed_numbers, "
                       "setting decimal_places=2; never copy "
                       "floating-point noise from the catalog. Preserve the sign and units. "
                       "Do not invent conditional price targets as observed facts.")
            prompt += ("\nEDITORIAL CONTRACT: Write for a financially literate person, not a software "
                       "engineer. Keep fact_catalog keys, snapshot IDs, boolean arrays and internal "
                       "policy names in structured references only, never in reader-facing prose. "
                       "Use familiar labels such as EMA 10, SMA 50, SMA 200, 90-day return, and "
                       "observed-period high, preserving the same digits in Vietnamese. Explain "
                       "uncertainty plainly; do not copy debating agents' metaphors. Vietnamese must "
                       "be natural financial writing: price action = diễn biến giá, trend structure = "
                       "cấu trúc xu hướng, pullback = nhịp điều chỉnh, invalidation = điều kiện làm "
                       "mất hiệu lực luận điểm. Avoid literal translations such as băng giá, ngăn xếp "
                       "cấu trúc, nạp lại tăng giá, lưỡi dao phòng thủ, điểm ngọt or cầu dao. "
                       "Summarize the strongest opposing evidence without repeating each agent's "
                       "entire argument. Do not prescribe sizing, even without a numeric quantity.")

        def capture_decision(value):
            nonlocal structured_decision
            # Revalidate even model instances: model_copy can bypass validators.
            validated = schema.model_validate(value.model_dump())
            if research_only and snapshot_reports is not None:
                from tradingagents.platform.analysis.research_validation import (
                    validate_canonical_report,
                )

                validate_canonical_report(validated, fact_sources, snapshot_ids)
            structured_decision = validated.model_dump(mode="json")

        final_trade_decision = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_pm_decision,
            "Portfolio Manager",
            on_structured=capture_decision,
            repair_schema=schema if research_only else None,
            diagnostics=diagnostics,
        )

        if research_only and structured_decision is not None:
            from tradingagents.agents.utils.report_localization import reader_report

            canonical = schema.model_validate(structured_decision)
            final_trade_decision = reader_report(canonical)

        new_risk_debate_state = {
            "judge_decision": final_trade_decision,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": final_trade_decision,
            "structured_decision": structured_decision,
            "structured_diagnostics": diagnostics,
        }

    return portfolio_manager_node
