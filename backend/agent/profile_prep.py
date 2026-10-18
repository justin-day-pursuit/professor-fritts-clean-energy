"""
Profile preparation: turns what the user typed (plus any uploaded bills) into the profile the agent reads.

Two jobs, both plain code with no Claude call:
  1. Tidy the intake: old field names are mapped to new ones, and a goal sentence is written from the
     goal percent when the user only moved the slider.
  2. Use uploaded bills: if annual use is blank and twelve months of bills were uploaded, their total
     becomes the annual use and is labeled "from your bills".

The stored session profile is never changed; the harness builds this effective copy for each run.
"""

from __future__ import annotations

from typing import Any

# Twelve monthly rows make a full year. Fewer is flagged, never scaled up quietly.
FULL_YEAR_MONTHS = 12
# If a typed annual use and the bills total differ by more than this share, the typed value is kept and flagged.
DISAGREE_SHARE = 0.10


def _blank(value: Any) -> bool:
    """True for None and empty or whitespace-only text; a real 0 is an answer."""
    return value is None or (isinstance(value, str) and value.strip() == "")


def normalize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """
    Return a tidied copy of the intake profile.

    - critical_load_hours (old name) becomes backup_hours_wanted when the new field is blank.
    - A blank goal is written from goal_percent (and target_year) so the plan has a goal sentence.
    """
    out = dict(profile)
    if _blank(out.get("backup_hours_wanted")) and not _blank(out.get("critical_load_hours")):
        out["backup_hours_wanted"] = out["critical_load_hours"]
    if _blank(out.get("goal")) and not _blank(out.get("goal_percent")):
        year = out.get("target_year")
        suffix = f" by {year}" if not _blank(year) else ""
        out["goal"] = f"Cut grid electricity use by {out['goal_percent']}%{suffix}"
    return out


def bills_total(documents: list[dict[str, Any]]) -> tuple[float, int] | None:
    """
    Add up the parsed bill uploads. Returns (total kWh, number of months) or None when no bills parsed.

    `documents` is a list of each upload's parsed_summary.
    """
    total = 0.0
    months = 0
    found = False
    for summary in documents:
        if not isinstance(summary, dict) or summary.get("type") != "bills":
            continue
        rows = summary.get("months") or []
        if not rows:
            continue
        found = True
        months += len(rows)
        total += sum(float(r.get("kwh") or 0) for r in rows)
    return (total, months) if found else None


def merge_bills(profile: dict[str, Any], documents: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Fill annual_kwh from uploaded bills when the user left it blank. Adds notes in profile["profile_flags"].

    - 12 or more months and annual_kwh blank: use the total, annual_kwh_source = "bills".
    - fewer than 12 months: leave annual_kwh as is and flag bills_incomplete.
    - typed value that disagrees with a full year of bills by over 10%: keep the typed value, flag it.
    """
    out = dict(profile)
    flags = list(out.get("profile_flags") or [])
    found = bills_total(documents)
    if found is None:
        out["profile_flags"] = flags
        return out
    total, months = found
    if months < FULL_YEAR_MONTHS:
        flags.append(f"bills_incomplete:{months}_months")
    elif _blank(out.get("annual_kwh")):
        out["annual_kwh"] = round(total)
        out["annual_kwh_source"] = "bills"
        flags.append("annual_kwh_from_bills")
    else:
        typed = float(out["annual_kwh"])
        if typed and abs(typed - total) / typed > DISAGREE_SHARE:
            flags.append(f"annual_kwh_disagrees_with_bills:typed_{round(typed)}_bills_{round(total)}")
    out["profile_flags"] = flags
    return out


def effective_profile(profile: dict[str, Any] | None, documents: list[dict[str, Any]]) -> dict[str, Any]:
    """The profile the agent runs on: tidied intake plus bills."""
    return merge_bills(normalize_profile(profile or {}), documents)
