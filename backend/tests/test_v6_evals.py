"""
v6 goalpost: every eval case passes in mock mode.

One test per fixture folder that has an expected.json, so a new case is picked up without editing
this file. The expectations themselves live in each case's expected.json (see agent/evals.py).
"""

from __future__ import annotations

import pytest

from agent.evals import list_eval_cases, run_eval_case


def test_all_nine_eval_cases_are_present():
    """The PRD's three cases plus the six v6 extra cases (outside NYC x2, no budget, DSIRE, flood, landmark)."""
    assert len(list_eval_cases()) >= 9


@pytest.mark.parametrize("case", list_eval_cases())
def test_eval_case_passes_in_mock_mode(case):
    """Run the case with the scripted model and mock tools and compare it to its expected.json."""
    result = run_eval_case(case)
    assert result.passed, "\n".join(result.failures)
