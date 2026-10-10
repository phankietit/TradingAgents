import pytest

from tradingagents.agents.utils.statement_anchors import non_standalone_anchors


@pytest.mark.parametrize("text", [
    "⟦QA⟧.", "Context. ⟦QA⟧. Interpretation.", "Context\n⟦QA⟧\nInterpretation.",
    "  ⟦QA⟧  ", "Context! ⟦QA⟧.", "{{QA}}. Context.",
])
def test_complete_owned_statement_has_its_own_sentence(text):
    anchors = ["⟦QA⟧", "{{QA}}"]
    assert non_standalone_anchors(text, anchors) == []


@pytest.mark.parametrize("text", [
    "Không đúng: ⟦QA⟧.", "⟦QA⟧ triệu USD.", "Assets were ${{QA}} billion.",
    "If ⟦QA⟧.", "Not ⟦QA⟧.", "'⟦QA⟧'.", "(⟦QA⟧).",
    "⟦QA⟧ of annual revenue.", "⟦QA⟧. Later, not ⟦QA⟧.",
])
def test_changed_unit_subject_condition_or_negation_cannot_wrap_owned_statement(text):
    anchors = ["⟦QA⟧", "{{QA}}"]
    assert len(non_standalone_anchors(text, anchors)) == 1
