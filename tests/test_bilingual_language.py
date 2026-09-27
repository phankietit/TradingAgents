"""Offline language instructions; no claims about live model translation accuracy."""
from tradingagents.agents.utils.agent_utils import get_language_instruction
from tradingagents.dataflows.config import set_config


def test_bilingual_instruction_preserves_financial_and_schema_contracts():
    set_config({"output_language": "English and Vietnamese"})
    instruction = get_language_instruction()
    for required in ("English:", "Tiếng Việt:", "numbers, signs, units, dates, tickers, citations",
                     "uncertainty, risks and invalidation conditions", "JSON keys, enum values and tool arguments unchanged",
                     "Do not add facts or strengthen conclusions", "human-readable string fields"):
        assert required in instruction


def test_existing_single_language_instructions_are_unchanged():
    set_config({"output_language": "English"})
    assert get_language_instruction() == ""
    set_config({"output_language": "Vietnamese"})
    assert get_language_instruction() == " Write your entire response in Vietnamese."
