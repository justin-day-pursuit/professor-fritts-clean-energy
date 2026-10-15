"""
Mock tool fixtures and calculate tool tests.
"""

from __future__ import annotations

import json
import os

import pytest
from django.conf import settings

from mocks.mock_mode import FIXTURES_ROOT, load_fixture
from tools.base import ToolResult
from tools.calculate import CalculateInput, run_calculate
from tools.registry import execute_tool, list_tool_names


CASE = "case1_queens_library"


@pytest.mark.parametrize("tool_name", list_tool_names())
def test_mock_fixtures_have_provenance(tool_name):
    if tool_name in ("get_building_profile", "calculate", "upsert_reference_cache"):
        pytest.skip("live/session/write tools have no fixture file")
    result = load_fixture(CASE, tool_name)
    assert result.source_url
    assert result.retrieved_at
    assert result.dataset_version
    assert result.mock is True


def test_calculate_c1_c4():
    c1 = run_calculate(CalculateInput(formula="C1", inputs={"roof_area_sqft": 6000, "setback_factor": 0.55}))
    assert c1.data["value"] == pytest.approx(3300.0)
    c2 = run_calculate(CalculateInput(formula="C2", inputs={"usable_roof_sqft": 3300, "sqft_per_kw": 66}))
    assert c2.data["value"] == pytest.approx(50.0, rel=0.01)
    c3 = run_calculate(CalculateInput(formula="C3", inputs={"annual_solar_kwh": 60000, "annual_use_kwh": 310000}))
    assert c3.data["value"] == pytest.approx(60000 / 310000, rel=0.01)
    c4 = run_calculate(CalculateInput(formula="C4", inputs={"annual_solar_kwh": 60000, "avg_rate_usd_per_kwh": 0.22}))
    assert c4.data["value"] == pytest.approx(13200.0, rel=0.01)


def _queens_profile() -> dict:
    """Dana's intake for eval case 1, read from the saved fixture."""
    return json.loads((FIXTURES_ROOT / CASE / "intake.json").read_text(encoding="utf-8"))


class _FakeResponse:
    """Stands in for an httpx response so the tests never touch the network."""
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        pass


def _fake_httpx_get(url, params=None, timeout=None):
    """Fake web call: the NYC geocoder or PVWatts, with PVWatts output that shrinks as losses grow."""
    if "geosearch" in url:
        return _FakeResponse(
            {
                "features": [
                    {
                        "geometry": {"coordinates": [-73.828843, 40.757744]},
                        "properties": {
                            "label": "41-17 MAIN STREET, Flushing, NY, USA",
                            "borough": "Queens",
                            "postalcode": "11355",
                            "match_type": "fallback",
                            "confidence": 0.8,
                        },
                    }
                ]
            }
        )
    losses = params["losses"]
    return _FakeResponse(
        {
            "errors": [],
            "version": "8.5.0",
            "outputs": {
                "ac_annual": 61893.6 * (100 - losses) / 86,  # 61,893.6 at the 14% default
                "capacity_factor": 14.13,
                "solrad_annual": 4.41,
                "ac_monthly": [1.0] * 12,
            },
            "station_info": {"weather_data_source": "NSRDB test"},
        }
    )


def test_live_mode_keeps_fixtures_for_tools_without_a_live_version(monkeypatch):
    """A tool with no live version still answers from its saved file, marked mock, when live mode is on."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    result = execute_tool("get_hazard_context", {}, session_profile={}, fixture_case=CASE)
    assert result.mock is True


def test_live_solar_returns_real_shaped_result(monkeypatch):
    """Live solar returns real-shaped output: array size from the roof, a kWh range, source and date, and no API key leaked."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("NLR_API_KEY", "test-key")
    monkeypatch.setattr("httpx.get", _fake_httpx_get)

    result = execute_tool("get_solar_production", {}, session_profile=_queens_profile(), fixture_case=CASE)

    assert result.mock is False
    assert result.data["system_kw_dc"] == pytest.approx(50.0)  # 6000 sq ft roof, C1 then C2
    assert result.data["annual_ac_kwh"] == pytest.approx(61893.6)
    assert result.data["capacity_factor"] == pytest.approx(0.1413)
    assert result.data["pvwatts_inputs"]["lat"] == pytest.approx(40.757744)
    assert result.source_url.startswith("https://developer.nlr.gov/")
    assert result.dataset_version == "pvwatts-v8.5.0"
    assert result.retrieved_at.endswith("Z")
    assert result.data["annual_ac_kwh_low"] == pytest.approx(61893.6 * 82 / 86)
    assert result.data["annual_ac_kwh_high"] == pytest.approx(61893.6 * 90 / 86)
    assert result.data["range_assumption"].startswith("ASSUMPTION")
    assert "address_match_approximate" not in result.flags
    assert "test-key" not in result.model_dump_json()


def test_live_solar_accepts_an_explicit_system_size(monkeypatch):
    """If the agent passes a system size in kW, the tool uses it instead of sizing from the roof."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("NLR_API_KEY", "test-key")
    monkeypatch.setattr("httpx.get", _fake_httpx_get)

    result = execute_tool("get_solar_production", {"system_kw": 30}, session_profile=_queens_profile(), fixture_case=CASE)

    assert result.data["system_kw_dc"] == 30


def test_live_solar_needs_an_api_key(monkeypatch):
    """Live solar stops with a clear message when NLR_API_KEY is missing."""
    from tools.live_solar import LiveSolarError

    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.delenv("NLR_API_KEY", raising=False)
    with pytest.raises(LiveSolarError, match="NLR_API_KEY"):
        execute_tool("get_solar_production", {}, session_profile=_queens_profile(), fixture_case=CASE)


def test_live_solar_needs_a_borough(monkeypatch):
    """Live solar stops when the borough is blank, so it cannot match a same-named street elsewhere."""
    from tools.live_solar import LiveSolarError

    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("NLR_API_KEY", "test-key")
    monkeypatch.setattr("httpx.get", _fake_httpx_get)
    profile = {**_queens_profile(), "borough": ""}
    with pytest.raises(LiveSolarError, match="borough"):
        execute_tool("get_solar_production", {}, session_profile=profile, fixture_case=CASE)


def _fake_eia_get(url, params=None, timeout=None):
    """Fake EIA reply: 12 months of prices, 24 cents for the newest six and 20 cents for the older six."""
    months = [f"2026-{m:02d}" for m in range(7, 0, -1)] + [f"2025-{m:02d}" for m in range(12, 7, -1)]
    prices = ["24.00"] * 6 + ["20.00"] * 6
    rows = [
        {"period": period, "price": price, "price-units": "cents per kilowatt-hour"}
        for period, price in zip(months, prices)
    ]
    return _FakeResponse({"response": {"data": rows}})


def test_live_rates_average_the_last_twelve_months(monkeypatch):
    """The rate is the 12-month average, with the latest month, low and high price, and the statewide flag."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("EIA_API_KEY", "test-key")
    monkeypatch.setattr("httpx.get", _fake_eia_get)

    result = execute_tool("get_utility_rates", {}, session_profile=_queens_profile(), fixture_case=CASE)

    assert result.mock is False
    assert result.data["avg_energy_charge_usd_per_kwh"] == pytest.approx(0.22)  # (6 x 24 + 6 x 20) / 12 cents
    assert result.data["latest_month_usd_per_kwh"] == pytest.approx(0.24)
    assert result.data["price_low_usd_per_kwh"] == pytest.approx(0.20)
    assert result.data["price_high_usd_per_kwh"] == pytest.approx(0.24)
    assert result.data["latest_month"] == "2026-07"
    assert result.data["period_start"] == "2025-08"
    assert result.dataset_version == "eia-retail-sales-2026-07"
    assert "statewide_average_rate" in result.flags
    assert "test-key" not in result.model_dump_json()


def test_live_rates_need_an_api_key(monkeypatch):
    """Live rates stop with a clear message when EIA_API_KEY is missing."""
    from tools.live_rates import LiveRatesError

    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    with pytest.raises(LiveRatesError, match="EIA_API_KEY"):
        execute_tool("get_utility_rates", {}, session_profile={}, fixture_case=CASE)


def _fake_records_get(url, params=None, timeout=None, headers=None):
    """Fake geocoder plus fake PLUTO row for the lot at 41-24 Kissena Boulevard."""
    if "geosearch" in url:
        response = _fake_httpx_get(url, params=params, timeout=timeout).json()
        response["features"][0]["properties"]["addendum"] = {"pad": {"bbl": "4050430011"}}
        return _FakeResponse(response)
    assert params["$where"] == "bbl=4050430011"
    return _FakeResponse(
        [
            {
                "address": "41-24 KISSENA BOULEVARD",
                "zipcode": "11355",
                "bldgarea": "75000",
                "lotarea": "18000",
                "numfloors": "3.0000000",
                "yearbuilt": "1996",
                "bldgclass": "P8",
                "landuse": "8",
                "landmark": None,
                "version": "25v3",
            }
        ]
    )


def test_live_records_report_the_city_record_and_flag_disagreements(monkeypatch):
    """The city record is returned as it is, and the fields that disagree with the intake are listed and flagged."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setattr("httpx.get", _fake_records_get)

    result = execute_tool("lookup_ny_building_records", {}, session_profile=_queens_profile(), fixture_case=CASE)

    assert result.mock is False
    assert result.data["gross_floor_area_sqft"] == 75000
    assert result.data["year_built"] == 1996
    assert result.data["landmark_flag"] is False
    assert result.dataset_version == "pluto-25v3"
    assert {d["field"] for d in result.data["differs_from_intake"]} == {"floor_area_sqft", "year_built"}
    assert "intake_mismatch:floor_area_sqft" in result.flags
    assert "intake_mismatch:year_built" in result.flags
    assert "address_street_mismatch" in result.flags
    assert result.data["lot_matches_intake_floor"] is True


def test_live_records_do_not_flag_a_matching_intake(monkeypatch):
    """No mismatch flags when the intake agrees with the city record."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setattr("httpx.get", _fake_records_get)
    profile = {**_queens_profile(), "floor_area_sqft": 75000, "year_built": 1996}

    result = execute_tool("lookup_ny_building_records", {}, session_profile=profile, fixture_case=CASE)

    assert result.data["differs_from_intake"] == []
    assert not [f for f in result.flags if f.startswith("intake_mismatch")]


def test_live_records_need_a_borough(monkeypatch):
    """Live records stop when the borough is blank."""
    from tools.live_records import LiveRecordsError

    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setattr("httpx.get", _fake_records_get)
    profile = {**_queens_profile(), "borough": ""}
    with pytest.raises(LiveRecordsError, match="borough"):
        execute_tool("lookup_ny_building_records", {}, session_profile=profile, fixture_case=CASE)


LIVE_FIXTURE_DIR = FIXTURES_ROOT / CASE / "live"


@pytest.mark.parametrize("tool_name", ["get_solar_production", "get_utility_rates", "lookup_ny_building_records"])
def test_saved_live_fixtures_have_provenance_and_no_secrets(tool_name):
    """The saved live responses are marked not mock, carry source, date and version, and hold no API key."""
    path = LIVE_FIXTURE_DIR / f"{tool_name}.json"
    result = ToolResult.model_validate_json(path.read_text(encoding="utf-8"))
    assert result.mock is False
    assert result.source_url.startswith("https://")
    assert result.retrieved_at.endswith("Z")
    assert result.dataset_version
    assert "api_key" not in path.read_text(encoding="utf-8").lower()


def test_low_confidence_geocode_is_flagged_as_approximate(monkeypatch):
    """A low-confidence address match is flagged so nobody trusts the wrong building."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("NLR_API_KEY", "test-key")

    def low_confidence_get(url, params=None, timeout=None):
        response = _fake_httpx_get(url, params=params, timeout=timeout)
        if "geosearch" in url:
            response.json()["features"][0]["properties"]["confidence"] = 0.4
        return response

    monkeypatch.setattr("httpx.get", low_confidence_get)
    result = execute_tool("get_solar_production", {}, session_profile=_queens_profile(), fixture_case=CASE)
    assert "address_match_approximate" in result.flags


def test_web_requests_retry_after_a_network_error(monkeypatch):
    """A request that fails once and then works succeeds on the retry."""
    import httpx

    from tools import web

    calls = []

    def flaky_get(url, **kwargs):
        calls.append(url)
        if len(calls) < 2:
            raise httpx.ConnectError("blip")
        return _FakeResponse({"ok": True})

    monkeypatch.setattr("httpx.get", flaky_get)
    monkeypatch.setattr(web.time, "sleep", lambda _s: None)
    assert web.get_with_retry("https://example.test").json() == {"ok": True}
    assert len(calls) == 2


def test_web_requests_give_up_after_the_retries(monkeypatch):
    """A service that stays down raises the error after the retries run out."""
    import httpx

    from tools import web

    def always_down(url, **kwargs):
        raise httpx.ConnectError("down")

    monkeypatch.setattr("httpx.get", always_down)
    monkeypatch.setattr(web.time, "sleep", lambda _s: None)
    with pytest.raises(httpx.ConnectError):
        web.get_with_retry("https://example.test")


def _case1_ranges(profile: dict) -> dict:
    """What a v1 answer needs: kWh and dollar ranges, each figure with a source or a calculation ID."""
    solar = execute_tool("get_solar_production", {}, session_profile=profile, fixture_case=CASE)
    rates = execute_tool("get_utility_rates", {}, session_profile=profile, fixture_case=CASE)
    low = run_calculate(
        CalculateInput(
            formula="C4",
            inputs={"annual_solar_kwh": solar.data["annual_ac_kwh_low"], "avg_rate_usd_per_kwh": rates.data["price_low_usd_per_kwh"]},
        )
    )
    high = run_calculate(
        CalculateInput(
            formula="C4",
            inputs={"annual_solar_kwh": solar.data["annual_ac_kwh_high"], "avg_rate_usd_per_kwh": rates.data["price_high_usd_per_kwh"]},
        )
    )
    return {"solar": solar, "rates": rates, "dollars_low": low, "dollars_high": high}


def test_case1_live_gives_kwh_and_dollar_ranges_with_sources(monkeypatch):
    """Case 1 live gives a kWh range and a dollar range (through calculation C4), each with a source or a calculation ID."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("NLR_API_KEY", "test-key")
    monkeypatch.setenv("EIA_API_KEY", "test-key")

    def route(url, **kwargs):
        if "eia.gov" in url:
            return _fake_eia_get(url, **kwargs)
        return _fake_httpx_get(url, params=kwargs.get("params"), timeout=kwargs.get("timeout"))

    monkeypatch.setattr("httpx.get", route)
    got = _case1_ranges(_queens_profile())

    assert got["solar"].data["annual_ac_kwh_low"] < got["solar"].data["annual_ac_kwh"] < got["solar"].data["annual_ac_kwh_high"]
    assert got["dollars_low"].data["value"] < got["dollars_high"].data["value"]
    assert got["dollars_low"].data["calc_id"] == "C4" and got["dollars_high"].data["calc_id"] == "C4"
    assert got["solar"].source_url and got["rates"].source_url


def test_live_solar_accepts_county_when_borough_is_empty(monkeypatch):
    """The form's "Borough or county" field can arrive as county; the live tools treat it as the borough."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("NLR_API_KEY", "test-key")
    monkeypatch.setattr("httpx.get", _fake_httpx_get)
    profile = {**_queens_profile(), "borough": "", "county": "Queens"}
    result = execute_tool("get_solar_production", {}, session_profile=profile, fixture_case=CASE)
    assert result.mock is False


def test_live_records_accept_county_when_borough_is_empty(monkeypatch):
    """Same as solar: a county value is used when the borough is empty, and the record reports it."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setattr("httpx.get", _fake_records_get)
    profile = {**_queens_profile(), "borough": "", "county": "Queens"}
    result = execute_tool("get_building_profile", {}, session_profile=profile, fixture_case=CASE)
    assert result.data["profile"]["county"] == "Queens"
    records = execute_tool("lookup_ny_building_records", {}, session_profile=profile, fixture_case=CASE)
    assert records.data["borough"] == "Queens"


@pytest.mark.parametrize("roof", [None, "", "abc", 0, -5])
def test_live_solar_rejects_a_missing_or_invalid_roof_area(monkeypatch, roof):
    """Without a system size, a missing, text, zero or negative roof area gives a clear error, not a KeyError."""
    from tools.live_solar import LiveSolarError

    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("NLR_API_KEY", "test-key")
    monkeypatch.setattr("httpx.get", _fake_httpx_get)
    profile = {k: v for k, v in _queens_profile().items() if k != "roof_area_sqft"}
    if roof is not None:
        profile["roof_area_sqft"] = roof
    with pytest.raises(LiveSolarError, match="roof area"):
        execute_tool("get_solar_production", {}, session_profile=profile, fixture_case=CASE)


def test_live_solar_does_not_need_roof_area_when_the_size_is_given(monkeypatch):
    """An explicit system size skips the roof-area sizing, so a missing roof area is fine."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("NLR_API_KEY", "test-key")
    monkeypatch.setattr("httpx.get", _fake_httpx_get)
    profile = {k: v for k, v in _queens_profile().items() if k != "roof_area_sqft"}
    result = execute_tool("get_solar_production", {"system_kw": 25}, session_profile=profile, fixture_case=CASE)
    assert result.data["system_kw_dc"] == 25


def test_geocoder_rejects_a_blank_address():
    """A blank or whitespace address gives a clear error instead of an IndexError."""
    from tools.geocode import GeocodeError, geocode_nyc_address

    for blank in ("", "   "):
        with pytest.raises(GeocodeError, match="No address"):
            geocode_nyc_address(blank, "Queens")


@pytest.mark.parametrize(
    ("address", "label", "fits"),
    [
        ("41-17 Main Street", "41-17 MAIN STREET, Flushing, NY, USA", True),
        ("4117 Main Street", "41-17 MAIN STREET, Flushing, NY, USA", True),  # hyphen ignored
        ("89-11 Merrick Blvd", "8911 MERRICK BOULEVARD, Jamaica, NY, USA", True),
        ("Queens Central Library", "89-11 MERRICK BOULEVARD, Jamaica, NY, USA", True),  # named building: no number to compare
        ("41-17 Main Street", "41-41 MAIN STREET, Flushing, NY, USA", False),
        ("41-1 Main Street", "41-17 MAIN STREET, Flushing, NY, USA", False),  # a prefix is not a match
        ("17 Main Street", "117 MAIN STREET, Brooklyn, NY, USA", False),
    ],
)
def test_house_number_check(address, label, fits):
    """The geocoder's match must start with the address's house number; named buildings pass through."""
    from tools.geocode import _house_number_fits

    assert _house_number_fits(address, label) is fits


def test_live_rates_ignore_months_with_no_price(monkeypatch):
    """A month with no price yet is skipped; with fewer than 12 priced months the tool stops with a clear error."""
    from tools.live_rates import LiveRatesError

    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    monkeypatch.setenv("EIA_API_KEY", "test-key")

    def partial_series(url, params=None, timeout=None):
        rows = _fake_eia_get(url).json()["response"]["data"]
        rows.insert(0, {"period": "2026-08", "price": None, "price-units": "cents per kilowatt-hour"})
        return _FakeResponse({"response": {"data": rows[: params["length"]]}})

    monkeypatch.setattr("httpx.get", partial_series)
    with pytest.raises(LiveRatesError, match="months with a price"):
        execute_tool("get_utility_rates", {}, session_profile={}, fixture_case=CASE)


@pytest.mark.skipif(os.environ.get("RUN_LIVE_TESTS") != "1", reason="set RUN_LIVE_TESTS=1 to call the real APIs")
def test_pvwatts_rerun_from_logged_inputs_matches_within_one_percent():
    """Real network: rerunning PVWatts from the saved inputs lands within 1% of the saved answer."""
    from tools.live_solar import rerun_pvwatts

    saved = ToolResult.model_validate_json((LIVE_FIXTURE_DIR / "get_solar_production.json").read_text(encoding="utf-8"))
    again = rerun_pvwatts(saved.data["pvwatts_inputs"], os.environ["NLR_API_KEY"])
    assert again["outputs"]["ac_annual"] == pytest.approx(saved.data["annual_ac_kwh"], rel=0.01)


@pytest.mark.skipif(os.environ.get("RUN_LIVE_TESTS") != "1", reason="set RUN_LIVE_TESTS=1 to call the real APIs")
def test_live_records_against_real_nyc_open_data(monkeypatch):
    """Real network: the Queens address returns a real tax lot with a floor area."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    result = execute_tool("lookup_ny_building_records", {}, session_profile=_queens_profile(), fixture_case=CASE)
    assert result.data["bbl"]
    assert result.data["gross_floor_area_sqft"] > 0


@pytest.mark.skipif(os.environ.get("RUN_LIVE_TESTS") != "1", reason="set RUN_LIVE_TESTS=1 to call the real APIs")
def test_live_rates_against_real_eia(monkeypatch):
    """Real network: the New York price from EIA is in a sane range."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    result = execute_tool("get_utility_rates", {}, session_profile=_queens_profile(), fixture_case=CASE)
    assert 0.10 < result.data["avg_energy_charge_usd_per_kwh"] < 0.50


@pytest.mark.skipif(os.environ.get("RUN_LIVE_TESTS") != "1", reason="set RUN_LIVE_TESTS=1 to call the real APIs")
def test_live_solar_against_real_apis(monkeypatch):
    """Real network: 50 kW at the Queens address makes a sane number of kWh."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    result = execute_tool("get_solar_production", {}, session_profile=_queens_profile(), fixture_case=CASE)
    assert 50000 < result.data["annual_ac_kwh"] < 75000


@pytest.mark.skipif(os.environ.get("RUN_LIVE_TESTS") != "1", reason="set RUN_LIVE_TESTS=1 to call the real APIs")
def test_case1_live_ranges_against_real_apis(monkeypatch):
    """Real network: the Case 1 dollar range is ordered low to high and in a sane range."""
    monkeypatch.setattr(settings, "TOOL_MODE", "live")
    got = _case1_ranges(_queens_profile())
    assert 5_000 < got["dollars_low"].data["value"] < got["dollars_high"].data["value"] < 30_000
