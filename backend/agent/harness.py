"""
Agent harness loop — Check 1 → think → (Check 2 → tool → Check 3 → notes)* → final → Check 4 → roadmap.

All ORM writes go through core.services; this module stays free of direct model queries except Session passed in.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from django.conf import settings
from pydantic import ValidationError

from agent.checks import run_check1, run_check2, run_check3, run_check4
from agent.claims import RoadmapPayload, RoadmapSection, WriteAnswerInput, WriteRoadmapInput
from agent.limits import MAX_CONSECUTIVE_THINK_STEPS, RunLimits
from agent.llm.base import LLMConfigurationError, LLMStep
from agent.llm.factory import get_llm_client
from agent.notes import AgentNotes
from agent.roadmap import render_roadmap_json, render_roadmap_markdown
from core.models import Run, Session
from core import services
from tools.cache import is_stale
from tools.registry import TOOL_SPECS, execute_tool, get_tool_spec


def load_system_prompt() -> str:
    """Read the v0 system prompt markdown shipped with the backend."""
    path = Path(__file__).resolve().parent / "prompts" / "system_prompt_v0.md"
    return path.read_text(encoding="utf-8")


def build_tool_schemas_for_llm() -> list[dict[str, Any]]:
    """
    JSON-schema-style tool definitions for the Anthropic API from TOOL_SPECS.

    Extend TOOL_SPECS when adding tools; this function picks up new entries automatically.
    """
    schemas: list[dict[str, Any]] = []
    for name, spec in sorted(TOOL_SPECS.items()):
        schemas.append(
            {
                "name": name,
                "description": spec.description,
                "input_schema": spec.input_model.model_json_schema(),
            }
        )
    return schemas


def _append_check_event(run: Run, seq: int, check_name: str, result: dict) -> int:
    services.append_event(run, seq=seq, kind=check_name, payload=dict(result))
    return seq + 1


def _finish_with_roadmap(
    run: Run,
    session: Session,
    *,
    seq: int,
    status: str,
    roadmap_payload: RoadmapPayload,
    final_tool_name: str,
    notes: AgentNotes,
    check4: dict,
    limits: RunLimits,
    t0: float,
) -> Run:
    """
    Shared exit path after Check 4 — store markdown/json, assistant message, and run status.

    Call this for done, partial, or exhausted scripted fix with an existing roadmap object.
    """
    rendered = render_roadmap_json(roadmap_payload)
    flags: dict[str, Any] = {"check4": check4}
    if status != Run.Status.DONE:
        notes.flags.append("check4_partial")
        flags["issues"] = check4.get("details", {}).get("issues", [])

    services.append_event(run, seq=seq, kind="final", payload={"status": status})
    assistant_text = render_roadmap_markdown(roadmap_payload)
    services.add_message(session, role="assistant", content=assistant_text, run=run)
    services.finish_run(
        run,
        status=status,
        output={
            "roadmap": roadmap_payload.model_dump(),
            "markdown": rendered["markdown"],
            "final_tool": final_tool_name,
            "notes": notes.model_dump(),
        },
        flags=flags,
        tool_call_count=limits.tool_call_count,
        elapsed_seconds=time.monotonic() - t0,
    )
    return run


def run_harness(
    session: Session,
    user_message: str,
    *,
    llm_provider: str | None = None,
    tool_mode: str | None = None,
) -> Run:
    """
    Execute one full agent run for a session and user message; return the finished Run row.

    Creates the Run, appends RunEvents, and stores roadmap markdown/json in run.output.
    """
    mode = tool_mode or getattr(settings, "TOOL_MODE", "mock")
    provider = llm_provider or getattr(settings, "LLM_PROVIDER", "anthropic")

    run = services.create_run(
        session,
        tool_mode=mode,
        llm_provider=provider,
        status=Run.Status.RUNNING,
    )
    seq = 0
    t0 = time.monotonic()

    check1 = run_check1(session.profile or {}, user_message)
    seq = _append_check_event(run, seq, "check1", check1)

    if not check1.get("passed"):
        c1_details = check1.get("details") or {}
        reason = c1_details.get("stop_reason")
        if reason == "needs_input":
            question = c1_details.get("question") or check1.get("message", "")
            services.add_message(session, role="assistant", content=question, run=run)
            services.finish_run(
                run,
                status=Run.Status.NEEDS_INPUT,
                output={"question": question},
                elapsed_seconds=time.monotonic() - t0,
            )
            return run
        services.finish_run(
            run,
            status=Run.Status.FAILED,
            output={"error": check1.get("message")},
            elapsed_seconds=time.monotonic() - t0,
        )
        return run

    try:
        llm = get_llm_client(provider, fixture_case=session.fixture_case)
    except LLMConfigurationError as exc:
        services.append_event(run, seq=seq, kind="error", payload={"message": exc.user_message()})
        services.finish_run(
            run,
            status=Run.Status.FAILED,
            output={"error": exc.user_message()},
            elapsed_seconds=time.monotonic() - t0,
        )
        return run

    llm.reset()
    notes = AgentNotes()
    limits = RunLimits()
    system_prompt = load_system_prompt()
    tool_schemas = build_tool_schemas_for_llm()
    fix_attempted = False
    fix_context: str | None = None
    roadmap_payload: RoadmapPayload | None = None
    final_tool_name = "write_roadmap"
    consecutive_thinks = 0

    while True:
        if limits.timeout_exceeded():
            services.append_event(run, seq=seq, kind="error", payload={"message": "timeout"})
            services.finish_run(
                run,
                status=Run.Status.FAILED,
                output={"error": "Run timed out"},
                tool_call_count=limits.tool_call_count,
                elapsed_seconds=time.monotonic() - t0,
            )
            return run

        try:
            step: LLMStep = llm.next_step(
                system_prompt=system_prompt,
                user_message=user_message,
                notes_summary=notes.summarize_for_llm(),
                tool_schemas=tool_schemas,
                fix_context=fix_context,
            )
        except LLMConfigurationError as exc:
            services.append_event(run, seq=seq, kind="error", payload={"message": exc.user_message()})
            services.finish_run(
                run,
                status=Run.Status.FAILED,
                output={"error": exc.user_message()},
                elapsed_seconds=time.monotonic() - t0,
            )
            return run
        except RuntimeError as exc:
            services.append_event(run, seq=seq, kind="error", payload={"message": str(exc)})
            if roadmap_payload is not None:
                check4 = {"passed": False, "message": str(exc)}
                return _finish_with_roadmap(
                    run,
                    session,
                    seq=seq,
                    status=Run.Status.PARTIAL,
                    roadmap_payload=roadmap_payload,
                    final_tool_name=final_tool_name,
                    notes=notes,
                    check4=check4,
                    limits=limits,
                    t0=t0,
                )
            services.finish_run(
                run,
                status=Run.Status.FAILED,
                output={"error": str(exc)},
                elapsed_seconds=time.monotonic() - t0,
            )
            return run

        fix_context = None

        if step.kind == "exhausted":
            if roadmap_payload is not None:
                check4 = {"passed": False, "message": step.message or "Scripted sequence exhausted."}
                return _finish_with_roadmap(
                    run,
                    session,
                    seq=seq,
                    status=Run.Status.PARTIAL,
                    roadmap_payload=roadmap_payload,
                    final_tool_name=final_tool_name,
                    notes=notes,
                    check4=check4,
                    limits=limits,
                    t0=t0,
                )
            services.append_event(
                run,
                seq=seq,
                kind="error",
                payload={"message": step.message or "LLM sequence exhausted."},
            )
            services.finish_run(
                run,
                status=Run.Status.FAILED,
                output={"error": step.message or "LLM sequence exhausted."},
                elapsed_seconds=time.monotonic() - t0,
            )
            return run

        if step.kind == "think":
            consecutive_thinks += 1
            services.append_event(run, seq=seq, kind="think", payload={"message": step.message})
            seq += 1
            if consecutive_thinks >= MAX_CONSECUTIVE_THINK_STEPS:
                msg = "Too many think steps in a row; stopping this run."
                services.append_event(run, seq=seq, kind="error", payload={"message": msg})
                services.finish_run(
                    run,
                    status=Run.Status.FAILED,
                    output={"error": msg},
                    tool_call_count=limits.tool_call_count,
                    elapsed_seconds=time.monotonic() - t0,
                )
                return run
            continue

        consecutive_thinks = 0

        if step.kind == "final":
            final_tool_name = step.tool_name or "write_roadmap"
            check2 = run_check2(final_tool_name, step.tool_input or {}, limits, is_final_tool=True)
            seq = _append_check_event(run, seq, "check2", check2)
            if not check2.get("passed"):
                services.finish_run(
                    run,
                    status=Run.Status.FAILED,
                    output={"error": check2.get("message")},
                    tool_call_count=limits.tool_call_count,
                    elapsed_seconds=time.monotonic() - t0,
                )
                return run

            try:
                if final_tool_name == "write_answer":
                    ans = WriteAnswerInput.model_validate(step.tool_input or {})
                    roadmap_payload = RoadmapPayload(
                        sections=[
                            RoadmapSection(
                                section_id="follow_up",
                                title="Follow-up answer",
                                claims=ans.claims,
                            )
                        ]
                    )
                else:
                    wr = WriteRoadmapInput.model_validate(step.tool_input or {})
                    roadmap_payload = wr.roadmap
            except ValidationError as exc:
                services.append_event(
                    run,
                    seq=seq,
                    kind="error",
                    payload={"validation_error": exc.errors(include_url=False)},
                )
                services.finish_run(
                    run,
                    status=Run.Status.FAILED,
                    output={"error": "Final roadmap payload failed validation."},
                    tool_call_count=limits.tool_call_count,
                    elapsed_seconds=time.monotonic() - t0,
                )
                return run

            check4 = run_check4(roadmap_payload)
            seq = _append_check_event(run, seq, "check4", check4)

            if not check4.get("passed") and not fix_attempted:
                fix_attempted = True
                issues = check4.get("details", {}).get("issues") or []
                for issue in issues:
                    flag = f"check4_issue: {issue}"
                    if flag not in notes.flags:
                        notes.flags.append(flag)
                fix_context = (
                    "Check 4 rejected the roadmap. Fix every issue below and call write_roadmap again:\n"
                    + "\n".join(f"- {item}" for item in issues)
                )
                llm.prepare_check4_retry(issues, user_message)
                services.append_event(
                    run,
                    seq=seq,
                    kind="think",
                    payload={"message": "Check 4 failed; requesting one fix pass.", "issues": issues},
                )
                seq += 1
                continue

            status = Run.Status.DONE if check4.get("passed") else Run.Status.PARTIAL
            return _finish_with_roadmap(
                run,
                session,
                seq=seq,
                status=status,
                roadmap_payload=roadmap_payload,
                final_tool_name=final_tool_name,
                notes=notes,
                check4=check4,
                limits=limits,
                t0=t0,
            )

        # Regular tool call
        tool_name = step.tool_name or ""
        tool_input = step.tool_input or {}
        check2 = run_check2(tool_name, tool_input, limits)
        seq = _append_check_event(run, seq, "check2", check2)
        if not check2.get("passed"):
            if check2.get("code") == "invalid_input":
                limits.record_failed_tool_attempt(tool_name)
            services.finish_run(
                run,
                status=Run.Status.FAILED,
                output={"error": check2.get("message")},
                tool_call_count=limits.tool_call_count,
                elapsed_seconds=time.monotonic() - t0,
            )
            return run

        limits.record_successful_tool_call(tool_name)
        services.append_event(
            run,
            seq=seq,
            kind="tool_call",
            payload={"tool": tool_name, "input": tool_input},
        )
        seq += 1

        try:
            result = execute_tool(
                tool_name,
                tool_input,
                session_profile=session.profile or {},
                fixture_case=session.fixture_case,
            )
        except Exception as exc:
            limits.record_failed_tool_attempt(tool_name)
            services.append_event(run, seq=seq, kind="error", payload={"message": str(exc)})
            services.finish_run(
                run,
                status=Run.Status.FAILED,
                output={"error": str(exc)},
                tool_call_count=limits.tool_call_count,
                elapsed_seconds=time.monotonic() - t0,
            )
            return run

        spec = get_tool_spec(tool_name)
        kind = spec.freshness_kind if spec else "default"
        stale = is_stale(result.retrieved_at, kind)
        result = result.model_copy(update={"stale": stale or result.stale})

        check3 = run_check3(result, freshness_kind=kind)
        seq = _append_check_event(run, seq, "check3", check3)
        if not check3.get("passed"):
            limits.record_failed_tool_attempt(tool_name)
            services.finish_run(
                run,
                status=Run.Status.FAILED,
                output={"error": check3.get("message"), "flags": check3.get("flags", [])},
                tool_call_count=limits.tool_call_count,
                elapsed_seconds=time.monotonic() - t0,
            )
            return run

        for flag in check3.get("flags") or check3.get("details", {}).get("flags") or []:
            if flag not in notes.flags:
                notes.flags.append(flag)

        services.append_event(
            run,
            seq=seq,
            kind="tool_result",
            payload=result.model_dump(),
        )
        seq += 1
        notes.record_tool_result(tool_name, result)

        if step.tool_use_id:
            llm.submit_tool_result(
                step.tool_use_id,
                json.dumps(result.model_dump()),
                notes.summarize_for_llm(),
            )

        services.append_event(run, seq=seq, kind="note_update", payload={"summary": notes.summarize_for_llm()})
        seq += 1
