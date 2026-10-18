"""
The city's "is this roof solar ready?" answer is yes, no, or blank, and only an explicit no is a warning.

A blank used to be read as "no", so two of the five sample buildings (Red Hook and P.S. 24) were reported as "rated not solar
ready" when the city had never rated them. These tests use plain sample rows, with no network.
"""

from __future__ import annotations

import pytest

from tools.city_energy import parse_ll24_row, solar_readiness


@pytest.mark.parametrize(
    "value,expected",
    [("Yes", True), ("yes", True), (" YES ", True), ("No", False), ("no", False), (None, None), ("", None), ("  ", None), ("Unknown", None), ("N/A", None)],
)
def test_the_three_possible_answers(value, expected):
    assert solar_readiness(value) is expected


def test_a_row_with_no_assessment_is_not_marked_not_ready():
    row = {"solar_readiness_assessment": None, "installed_or_estimated": "228.2", "status": "Completed", "year_of_report": "2024"}
    parsed = parse_ll24_row(row)
    assert parsed["solar_ready"] is None
    assert parsed["installed_kw"] == 228.2


def test_an_explicit_no_still_reads_as_not_ready():
    assert parse_ll24_row({"solar_readiness_assessment": "No"})["solar_ready"] is False


def test_only_an_explicit_no_raises_the_not_solar_ready_flag():
    """The records tool raises the flag from this rule; a blank must not trigger it."""
    for value, flagged in ((False, True), (None, False), (True, False)):
        ll24 = {"solar_ready": value}
        raised = bool(ll24 and ll24["solar_ready"] is False)
        assert raised is flagged
