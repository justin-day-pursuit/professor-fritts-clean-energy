"""
The entered floor area is compared with the city's energy report, the same report the electricity use comes from.

Before, the form was filled from the tax lot while the planner also read the energy report, so two city records could
disagree with each other even though the visitor typed nothing wrong. These tests cover the comparison only; they use no
network and no Claude.
"""

from __future__ import annotations

from tools.live_records import _floor_area_difference, _street_name


def test_a_floor_area_close_to_the_city_figure_is_not_a_difference():
    assert _floor_area_difference({"floor_area_sqft": 43_760}, 43_760) is None
    assert _floor_area_difference({"floor_area_sqft": 40_000}, 43_760) is None  # within the tolerance


def test_a_floor_area_far_from_the_city_figure_is_reported_with_both_numbers():
    assert _floor_area_difference({"floor_area_sqft": 17_620}, 55_860) == {
        "field": "floor_area_sqft",
        "intake": 17_620,
        "city_record": 55_860,
    }


def test_nothing_is_compared_when_either_side_has_no_number():
    assert _floor_area_difference({}, 43_760) is None
    assert _floor_area_difference({"floor_area_sqft": 20_000}, None) is None


def test_the_street_a_visitor_picked_matches_the_street_the_geocoder_returns():
    # A lot listed under another frontage (155 Bay Street vs 140 Lorraine Street) is not a mismatch: only the street the
    # geocoder returned for the picked address is compared, and that is the same street the visitor picked.
    assert _street_name("155 BAY STREET") == _street_name("155 Bay Street, Brooklyn, New York, NY, USA".split(",")[0])
