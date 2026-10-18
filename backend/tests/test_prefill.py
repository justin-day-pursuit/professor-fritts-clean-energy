"""
Form pre-fill from free city records: the values, their sources, and what happens when a record is missing.

Nothing here touches the network or Claude. The builder is given sample records, and the route test replaces the three
city lookups with fakes, so it checks only how the answers are put together.
"""

from __future__ import annotations

import pytest

from tools.prefill import build_prefill

BBL = "2043050001"

# What the city's energy report and roof assessment look like after they have been read (see tools/city_energy.py).
LL84 = {"electricity_kwh": 482_913.4, "report_year": 2022}
LL24 = {"roof_condition": "Fair", "roof_age": "12", "solar_ready": False, "installed_kw": 0.0, "report_year": 2021}
ROOF = {"suggested_roof_area_sqft": 18_400, "building_count": 2, "source_url": "https://example.test/footprints", "note": "A suggestion."}


def _by_field(result: dict) -> dict:
    """The items keyed by their field name, so a test can look one up."""
    return {item["field"]: item for item in result["items"]}


def test_every_record_found_fills_every_value():
    result = build_prefill(BBL, LL84, LL24, ROOF)
    items = _by_field(result)
    assert set(items) == {"annual_kwh", "roof_condition", "solar_ready", "roof_area_sqft"}
    assert items["annual_kwh"]["value"] == 482_913
    assert items["annual_kwh"]["display"] == "482,913 kWh"
    assert items["roof_condition"]["display"] == "Fair, roof age 12"
    assert items["solar_ready"]["value"] is False
    assert items["roof_area_sqft"]["value"] == 18_400
    assert result["missing"] == []
    assert result["bbl"] == BBL


def test_every_value_names_its_source_and_asks_for_confirmation():
    for item in build_prefill(BBL, LL84, LL24, ROOF)["items"]:
        assert item["source"], item["field"]
        assert item["source_url"].startswith("https://"), item["field"]
        assert item["note"], item["field"]


def test_solar_already_installed_is_listed_only_when_the_city_reports_some():
    with_solar = build_prefill(BBL, LL84, {**LL24, "installed_kw": 150.0, "status": "Completed"}, ROOF)
    assert _by_field(with_solar)["existing_solar_kw"]["display"] == "150 kW installed"
    assert "existing_solar_kw" not in _by_field(build_prefill(BBL, LL84, LL24, ROOF))


def test_solar_that_is_only_planned_is_not_filled_in_as_already_on_the_roof():
    result = build_prefill(BBL, LL84, {**LL24, "installed_kw": 219.0, "status": "In Progress"}, ROOF)
    assert "existing_solar_kw" not in _by_field(result)
    assert any("planned or in progress" in line for line in result["missing"])


def test_a_blank_solar_readiness_is_not_reported_as_not_ready():
    # The city left the field blank: say nothing about readiness rather than "not solar ready".
    result = build_prefill(BBL, LL84, {**LL24, "solar_ready": None}, ROOF)
    assert "solar_ready" not in _by_field(result)
    assert "roof_condition" in _by_field(result)


def test_an_explicit_no_is_reported_as_not_ready():
    items = _by_field(build_prefill(BBL, LL84, {**LL24, "solar_ready": False}, ROOF))
    assert items["solar_ready"]["display"] == "Rated not solar ready by the city"


def test_a_solar_ready_roof_is_said_plainly():
    items = _by_field(build_prefill(BBL, LL84, {**LL24, "solar_ready": True}, ROOF))
    assert items["solar_ready"]["display"] == "Rated solar ready by the city"


@pytest.mark.parametrize("kwh", [None, 0, 0.0, "Not Available"])
def test_electricity_that_is_not_reported_is_left_blank_not_zero(kwh):
    result = build_prefill(BBL, {"electricity_kwh": kwh, "report_year": 2022}, LL24, ROOF)
    assert "annual_kwh" not in _by_field(result)
    assert any("no energy report" in line for line in result["missing"])


def test_a_building_the_city_has_no_records_for_gets_no_values_and_clear_sentences():
    result = build_prefill(BBL, None, None, None)
    assert result["items"] == []
    assert len(result["missing"]) == 3
    assert all("no " in line for line in result["missing"])


def test_a_service_that_did_not_answer_is_not_mistaken_for_a_missing_record():
    result = build_prefill(BBL, None, LL24, ROOF, problems={"energy": "unreachable"})
    assert any("did not answer" in line for line in result["missing"])
    assert not any("no energy report" in line for line in result["missing"])
    # The other records still fill in.
    assert {"roof_condition", "roof_area_sqft"} <= set(_by_field(result))


def test_a_roof_assessment_with_no_condition_still_reports_solar_readiness():
    items = _by_field(build_prefill(BBL, LL84, {"solar_ready": True, "roof_condition": None}, ROOF))
    assert "roof_condition" not in items
    assert items["solar_ready"]["value"] is True


# ----------------------------------------------------------------------------------------------------- the route


@pytest.fixture
def fake_city(monkeypatch):
    """Replace the three city lookups with answers set by each test, so no test reaches the network."""
    from api.routers import records

    answers = {"ll84": LL84, "ll24": LL24, "roof": ROOF}

    def respond(name):
        def fake(*_args, **_kwargs):
            value = answers[name]
            if isinstance(value, Exception):
                raise value
            return value

        return fake

    monkeypatch.setattr(records, "fetch_ll84", respond("ll84"))
    monkeypatch.setattr(records, "fetch_ll24", respond("ll24"))
    monkeypatch.setattr(records, "suggest_roof_area", respond("roof"))
    return answers


URL = f"/api/records/building-prefill?bbl={BBL}&address=1 Main St&borough=Bronx"


def test_the_route_returns_the_values(api_client, fake_city):
    response = api_client.get(URL)
    assert response.status_code == 200
    body = response.json()
    assert body["bbl"] == BBL
    assert {item["field"] for item in body["items"]} == {"annual_kwh", "roof_condition", "solar_ready", "roof_area_sqft"}


def test_the_route_still_answers_when_one_city_service_is_down(api_client, fake_city):
    from tools.city_energy import CityEnergyError

    fake_city["ll84"] = CityEnergyError("down")
    response = api_client.get(URL)
    assert response.status_code == 200
    body = response.json()
    assert "annual_kwh" not in {item["field"] for item in body["items"]}
    assert any("did not answer" in line for line in body["missing"])


def test_the_route_treats_an_address_the_geocoder_cannot_place_as_no_roof_outline(api_client, fake_city):
    from tools.geocode import GeocodeError

    fake_city["roof"] = GeocodeError("not found")
    body = api_client.get(URL).json()
    assert "roof_area_sqft" not in {item["field"] for item in body["items"]}
    assert any("no building outline" in line for line in body["missing"])


@pytest.mark.parametrize("bbl", ["123", "abcdefghij", "20430500011"])
def test_the_route_rejects_a_lot_number_that_is_not_ten_digits(api_client, fake_city, bbl):
    response = api_client.get(f"/api/records/building-prefill?bbl={bbl}&address=1 Main St")
    assert response.status_code == 422
