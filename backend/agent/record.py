"""
Record a finished run as a replayable case (v6, for demos and UI work).

A live run costs money and takes about two minutes. A recorded case replays the same run for free and
instantly: the scripted model plays back the tool calls Claude made and the final plan it wrote, and our
real code does everything else (the tools on the saved real data, all four checks, and the roadmap builder).

What is saved, in mocks/fixtures/<case>/:
  intake.json        the building profile and the question the run was given
  scripted_llm.json  the tool calls in order, then the final plan exactly as Claude wrote it
  <tool>.json        each outside tool's answer in that run (building records, solar, prices, hazard, ...)

The plan text is Claude's own, not rewritten here. A replay is therefore a recording of a real run, and should
be described as one. The tools that are plain code (calculate, run_financial_model) are not saved: they run again
and give the same numbers. Replays always run in mock mode, so the saved answers are used instead of live lookups.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mocks.catalog import FIXTURES_ROOT

# Tools whose answer comes from outside our code, so a replay needs the saved answer to give the same result.
FIXTURE_TOOLS = (
    "lookup_ny_building_records",
    "get_solar_production",
    "get_utility_rates",
    "get_utility_tariff",
    "search_ny_incentives_and_rules",
    "get_hazard_context",
    "optimize_solar_storage",
)


class RecordError(RuntimeError):
    """The run cannot be recorded (for example, it never produced a plan)."""


def _final_step(output: dict[str, Any]) -> dict[str, Any]:
    """The scripted final step, rebuilt from the plan the run stored."""
    roadmap = output.get("roadmap")
    if not roadmap:
        raise RecordError("This run has no plan to record (it stopped before writing one).")
    if output.get("final_tool") == "write_answer":
        claims = [claim for section in roadmap.get("sections", []) for claim in section.get("claims", [])]
        return {"type": "final", "name": "write_answer", "input": {"summary": output.get("summary", ""), "claims": claims}}
    return {"type": "final", "name": "write_roadmap", "input": {"roadmap": roadmap}}


def cost_ranges_from_notes(calculations: dict[str, Any]) -> dict[str, Any]:
    """
    The solar and battery price ranges (with where they came from) that a run's scenarios used, or {} for a run
    that used the placeholder prices. Read from the first scenario result that carries each one.
    """
    ranges: dict[str, Any] = {}
    for data in calculations.values():
        if not isinstance(data, dict):
            continue
        for key, price_key, basis_key, url_key in (
            ("solar", "solar_usd_per_kw", "solar_price_basis", "solar_price_source_url"),
            ("battery", "battery_usd_per_kwh", "battery_price_basis", "battery_price_source_url"),
        ):
            if key not in ranges and data.get(price_key) and data.get(basis_key):
                ranges[key] = {
                    "low": data[price_key][0],
                    "high": data[price_key][1],
                    "mid": data.get(price_key + "_mid"),
                    "basis": data[basis_key],
                    "source_url": data.get(url_key),
                }
        if "efficiency" not in ranges and data.get("efficiency_usd_per_kwh") and data.get("efficiency_price_basis"):
            ranges["efficiency"] = {
                "prices": data["efficiency_usd_per_kwh"],
                "mid": data.get("efficiency_usd_per_kwh_mid"),
                "basis": data["efficiency_price_basis"],
                "source_url": data.get("efficiency_price_source_url"),
            }
        if "realization" not in ranges and data.get("efficiency_realization"):
            ranges["realization"] = data["efficiency_realization"]
    return ranges


def record_run(run: Any, case: str, *, root: Path | None = None, overwrite: bool = False) -> dict[str, Any]:
    """
    Write the files for a replayable case from a stored run, and say what was written and what was left alone.

    Files that already exist in the case folder are kept unless overwrite is True, so a hand-made intake or a
    real data file is not lost by accident. scripted_llm.json is always rewritten, because it is the recording.
    Returns {"case", "written", "kept", "warnings", "tool_calls"}.
    """
    root = root or FIXTURES_ROOT
    folder = root / case
    folder.mkdir(parents=True, exist_ok=True)
    events = list(run.events.order_by("seq"))
    output = run.output or {}
    final = _final_step(output)

    written: list[str] = []
    kept: list[str] = []
    warnings: list[str] = []

    steps: list[dict[str, Any]] = [{"type": "think", "message": "Reviewing the intake and the question."}]
    for event in events:
        if event.kind == "tool_call":
            steps.append({"type": "tool", "name": event.payload.get("tool"), "input": event.payload.get("input") or {}})
    steps.append(final)
    (folder / "scripted_llm.json").write_text(
        json.dumps(
            {"_comment": f"Recording of live run {run.pk} (status {run.status}); the plan is the model's own words.", "steps": steps},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    written.append("scripted_llm.json")

    # The last answer for each outside tool wins, which is the one the plan was written from.
    results: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.kind == "tool_result" and event.payload.get("tool") in FIXTURE_TOOLS:
            if (event.payload.get("data") or {}).get("quarantined"):
                warnings.append(f"{event.payload['tool']}: the answer was withheld for hidden instructions, so it is not saved.")
                continue
            results[event.payload["tool"]] = event.payload
    called = {step["name"] for step in steps if step.get("type") == "tool"}
    for tool in sorted(called & set(FIXTURE_TOOLS) - set(results)):
        warnings.append(f"{tool}: the run called it but it returned no answer, so a replay will report it as failed too.")
    for tool, payload in results.items():
        name = f"{tool}.json"
        if (folder / name).exists() and not overwrite:
            kept.append(name)
            continue
        (folder / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(name)

    # The real prices a live run used (NYSERDA project costs), so a free replay prices the scenarios the same way.
    ranges = cost_ranges_from_notes((output.get("notes") or {}).get("calculations") or {})
    if ranges:
        (folder / "cost_ranges.json").write_text(json.dumps(ranges, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append("cost_ranges.json")

    if (folder / "intake.json").exists() and not overwrite:
        kept.append("intake.json")
    else:
        first_user = run.session.messages.filter(role="user").order_by("id").first()
        profile = dict(run.session.profile or {})
        if first_user:
            profile["question"] = first_user.content
        (folder / "intake.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append("intake.json")

    return {
        "case": case,
        "written": written,
        "kept": kept,
        "warnings": warnings,
        "tool_calls": len([s for s in steps if s.get("type") == "tool"]),
    }
