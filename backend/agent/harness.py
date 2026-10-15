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

from agent.checks import inspect_raw_roadmap, run_check1, run_check2, run_check3, run_check4, salvage_roadmap
from agent.claims import RoadmapPayload, RoadmapSection, WriteAnswerInput, WriteRoadmapInput
from agent.limits import MAX_CONSECUTIVE_THINK_STEPS, RunLimits
from agent.llm.base import LLMConfigurationError, LLMStep
from agent.llm.factory import get_llm_client
from agent.notes import AgentNotes
from agent.roadmap import render_follow_up_markdown, render_roadmap_json, render_roadmap_markdown
from core.models import Run, Session
from core import services
from tools.cache import is_stale_for_tool
from tools.registry import TOOL_SPECS, execute_tool, get_tool_spec


def load_system_prompt() -> str:
    """Read the v3 system prompt markdown shipped with the backend (v0–v2 stay in prompts/ for history)."""
    path = Path(__file__).resolve().parent / "prompts" / "system_prompt_v3.md"
    return path.read_text(encoding="utf-8")


def _tool_error_text(exc: Exception) -> str:
    """Readable text for a tool failure; a bare KeyError would otherwise show only the missing name."""
    if isinstance(exc, KeyError):
        return f"missing required input {exc}"
    return str(exc) or type(exc).__name__


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


def _close_run(
    run: Run,
    *,
    seq: int,
    status: str,
    output: dict,
    t0: float,
    tool_call_count: int = 0,
    flags: dict | None = None,
) -> Run:
    """
    End a run that stopped short of a roadmap and record that thinking finished.

    Pass the next free event number. If you just wrote an error at `seq`, pass `seq + 1`
    so the final line does not reuse that number. The dev trace page looks for this
    `final` event even when the status is failed or needs_input.
    """
    services.append_event(
        run,
        seq=seq,
        kind="final",
        payload={"status": status, "ended": True},
    )
    services.finish_run(
        run,
        status=status,
        output=output,
        flags=flags,
        tool_call_count=tool_call_count,
        elapsed_seconds=time.monotonic() - t0,
    )
    return run


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
    answer_summary: str | None = None,
    extra_run_flags: dict[str, Any] | None = None,
    skip_check4_partial_flag: bool = False,
) -> Run:
    """
    Shared exit path after Check 4 — store markdown/json, assistant message, and run status.

    Call this for done, partial, or exhausted scripted fix with an existing roadmap object.
    Pass answer_summary when the final tool was write_answer so the main text is not dropped.
    """
    rendered = render_roadmap_json(roadmap_payload)
    markdown_out = rendered["markdown"]
    if final_tool_name == "write_answer" and answer_summary:
        markdown_out = render_follow_up_markdown(answer_summary, roadmap_payload)
    flags: dict[str, Any] = {"check4": check4}
    if extra_run_flags:
        flags.update(extra_run_flags)
    if status != Run.Status.DONE and not skip_check4_partial_flag:
        notes.flags.append("check4_partial")
        flags["issues"] = check4.get("details", {}).get("issues", [])

    services.append_event(run, seq=seq, kind="final", payload={"status": status, "ended": True})
    if final_tool_name == "write_answer" and answer_summary:
        assistant_text = render_follow_up_markdown(answer_summary, roadmap_payload)
    else:
        assistant_text = render_roadmap_markdown(roadmap_payload)

    output: dict[str, Any] = {
        "roadmap": roadmap_payload.model_dump(),
        "markdown": markdown_out,
        "final_tool": final_tool_name,
        "notes": notes.model_dump(),
    }
    if answer_summary is not None:
        output["summary"] = answer_summary

    services.add_message(session, role="assistant", content=assistant_text, run=run)
    services.finish_run(
        run,
        status=status,
        output=output,
        flags=flags,
        tool_call_count=limits.tool_call_count,
        elapsed_seconds=time.monotonic() - t0,
    )
    return run


def _finish_think_cap_stop(
    run: Run,
    session: Session,
    *,
    seq: int,
    msg: str,
    notes: AgentNotes,
    limits: RunLimits,
    t0: float,
    roadmap_payload: RoadmapPayload | None,
    final_tool_name: str,
    answer_summary: str | None,
    check4: dict | None,
) -> Run:
    """
    Stop the run after too many think-only steps — always partial, never a hard failed cap.

    When a roadmap or answer already exists, attach it like other partial exits; otherwise
    store only flags and a short message (no invented roadmap). Update MAX_CONSECUTIVE_THINK_STEPS
    in limits.py if the cap changes.
    """
    notes.flags.append("think_cap_exceeded")
    services.append_event(run, seq=seq, kind="error", payload={"message": msg, "think_cap": True})
    seq += 1

    cap_check4 = check4 or {"passed": False, "message": msg, "code": "think_cap"}
    extra = {"think_cap_exceeded": True, "stop_reason": "think_cap"}

    if roadmap_payload is not None:
        return _finish_with_roadmap(
            run,
            session,
            seq=seq,
            status=Run.Status.PARTIAL,
            roadmap_payload=roadmap_payload,
            final_tool_name=final_tool_name,
            notes=notes,
            check4=cap_check4,
            limits=limits,
            t0=t0,
            answer_summary=answer_summary,
            extra_run_flags=extra,
            skip_check4_partial_flag=True,
        )

    services.append_event(
        run, seq=seq, kind="final", payload={"status": Run.Status.PARTIAL, "ended": True}
    )
    services.finish_run(
        run,
        status=Run.Status.PARTIAL,
        output={"message": msg, "notes": notes.model_dump()},
        flags=extra,
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
            return _close_run(
                run,
                seq=seq,
                status=Run.Status.NEEDS_INPUT,
                output={"question": question},
                t0=t0,
            )
        return _close_run(
            run,
            seq=seq,
            status=Run.Status.FAILED,
            output={"error": check1.get("message")},
            t0=t0,
        )

    try:
        llm = get_llm_client(provider, fixture_case=session.fixture_case)
    except LLMConfigurationError as exc:
        services.append_event(run, seq=seq, kind="error", payload={"message": exc.user_message()})
        return _close_run(
            run,
            seq=seq + 1,
            status=Run.Status.FAILED,
            output={"error": exc.user_message()},
            t0=t0,
        )

    llm.reset()
    notes = AgentNotes()
    limits = RunLimits()
    system_prompt = load_system_prompt()
    tool_schemas = build_tool_schemas_for_llm()
    fix_attempted = False
    fix_context: str | None = None
    roadmap_payload: RoadmapPayload | None = None
    answer_summary: str | None = None
    last_check4: dict[str, Any] | None = None
    final_tool_name = "write_roadmap"
    consecutive_thinks = 0

    while True:
        if limits.timeout_exceeded():
            services.append_event(run, seq=seq, kind="error", payload={"message": "timeout"})
            return _close_run(
                run,
                seq=seq + 1,
                status=Run.Status.FAILED,
                output={"error": "Run timed out"},
                t0=t0,
                tool_call_count=limits.tool_call_count,
            )

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
            return _close_run(
                run,
                seq=seq + 1,
                status=Run.Status.FAILED,
                output={"error": exc.user_message()},
                t0=t0,
                tool_call_count=limits.tool_call_count,
            )
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
            return _close_run(
                run,
                seq=seq + 1,
                status=Run.Status.FAILED,
                output={"error": str(exc)},
                t0=t0,
                tool_call_count=limits.tool_call_count,
            )

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
            return _close_run(
                run,
                seq=seq + 1,
                status=Run.Status.FAILED,
                output={"error": step.message or "LLM sequence exhausted."},
                t0=t0,
                tool_call_count=limits.tool_call_count,
            )

        if step.kind == "think":
            consecutive_thinks += 1
            services.append_event(run, seq=seq, kind="think", payload={"message": step.message})
            seq += 1
            if consecutive_thinks >= MAX_CONSECUTIVE_THINK_STEPS:
                msg = "Too many think steps in a row; stopping this run."
                return _finish_think_cap_stop(
                    run,
                    session,
                    seq=seq,
                    msg=msg,
                    notes=notes,
                    limits=limits,
                    t0=t0,
                    roadmap_payload=roadmap_payload,
                    final_tool_name=final_tool_name,
                    answer_summary=answer_summary,
                    check4=last_check4,
                )
            continue

        consecutive_thinks = 0

        if step.kind == "final":
            final_tool_name = step.tool_name or "write_roadmap"
            check2 = run_check2(final_tool_name, step.tool_input or {}, limits, is_final_tool=True)
            seq = _append_check_event(run, seq, "check2", check2)
            if not check2.get("passed"):
                return _close_run(
                    run,
                    seq=seq,
                    status=Run.Status.FAILED,
                    output={"error": check2.get("message")},
                    t0=t0,
                    tool_call_count=limits.tool_call_count,
                )

            roadmap_payload: RoadmapPayload | None = None
            answer_summary = None
            check4: dict[str, Any] | None = None
            try:
                if final_tool_name == "write_answer":
                    ans = WriteAnswerInput.model_validate(step.tool_input or {})
                    answer_summary = ans.summary
                    roadmap_payload = RoadmapPayload(
                        sections=[
                            RoadmapSection(
                                section_id="follow_up",
                                title="Follow-up answer",
                                claims=ans.claims,
                            )
                        ]
                    )
                    # A follow-up is not a 13-section plan. Referrals and labels still apply.
                    check4 = run_check4(
                        roadmap_payload,
                        assumptions_register=notes.assumptions,
                        user_message=user_message,
                        require_all_sections=False,
                    )
                else:
                    wr = WriteRoadmapInput.model_validate(step.tool_input or {})
                    roadmap_payload = wr.roadmap
                    answer_summary = None
                    check4 = run_check4(
                        roadmap_payload,
                        assumptions_register=notes.assumptions,
                        user_message=user_message,
                        require_all_sections=True,
                    )
            except ValidationError as exc:
                # A missing label never becomes a Claim. Treat that as a Check 4 miss so the
                # agent gets one fix pass, then a partial roadmap, instead of a hard stop.
                raw_roadmap = (step.tool_input or {}).get("roadmap")
                raw_issues = (
                    inspect_raw_roadmap(raw_roadmap, user_message=user_message)
                    if final_tool_name != "write_answer" and isinstance(raw_roadmap, dict)
                    else []
                )
                if raw_issues:
                    roadmap_payload = salvage_roadmap(raw_roadmap if isinstance(raw_roadmap, dict) else {})
                    check4 = {
                        "passed": False,
                        "code": "check4_fail",
                        "message": "; ".join(raw_issues),
                        "details": {"issues": raw_issues},
                    }
                else:
                    services.append_event(
                        run,
                        seq=seq,
                        kind="error",
                        payload={"validation_error": exc.errors(include_url=False)},
                    )
                    return _close_run(
                        run,
                        seq=seq + 1,
                        status=Run.Status.FAILED,
                        output={"error": "Final roadmap payload failed validation."},
                        t0=t0,
                        tool_call_count=limits.tool_call_count,
                    )

            if roadmap_payload is None or check4 is None:
                return _close_run(
                    run,
                    seq=seq,
                    status=Run.Status.FAILED,
                    output={"error": "Final roadmap payload failed validation."},
                    t0=t0,
                    tool_call_count=limits.tool_call_count,
                )
            last_check4 = check4
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
                # Anthropic requires a tool_result for the pending write_* before the next request.
                if step.tool_use_id:
                    llm.submit_tool_result(
                        step.tool_use_id,
                        json.dumps({"ok": False, "check4_issues": issues}),
                        notes.summarize_for_llm(),
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
                answer_summary=answer_summary,
            )

        # Regular tool call
        tool_name = step.tool_name or ""
        tool_input = step.tool_input or {}
        check2 = run_check2(tool_name, tool_input, limits)
        seq = _append_check_event(run, seq, "check2", check2)
        if not check2.get("passed"):
            if check2.get("code") == "invalid_input":
                limits.record_failed_tool_attempt(tool_name)
            return _close_run(
                run,
                seq=seq,
                status=Run.Status.FAILED,
                output={"error": check2.get("message")},
                t0=t0,
                tool_call_count=limits.tool_call_count,
            )

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
            error_text = _tool_error_text(exc)
            # With a real model (it supplies a tool_use id), hand the error back as the tool result so it
            # can fix its input or carry on without the tool. Check 2 still caps repeated failures per tool.
            # The scripted model has no tool_use id and cannot react, so that case still ends the run.
            services.append_event(
                run,
                seq=seq,
                kind="error",
                payload={"message": error_text, "tool": tool_name, "will_retry": bool(step.tool_use_id)},
            )
            seq += 1
            if step.tool_use_id:
                llm.submit_tool_result(
                    step.tool_use_id,
                    json.dumps(
                        {
                            "error": error_text,
                            "tool": tool_name,
                            "instruction": "The tool did not run. Fix the input and call it again, "
                            "or continue without it and say in the roadmap what is missing.",
                        }
                    ),
                    notes.summarize_for_llm(),
                )
                continue
            return _close_run(
                run,
                seq=seq,
                status=Run.Status.FAILED,
                output={"error": error_text},
                t0=t0,
                tool_call_count=limits.tool_call_count,
            )

        spec = get_tool_spec(tool_name)
        kind = spec.freshness_kind if spec else "default"
        stale = is_stale_for_tool(tool_name, result.retrieved_at, kind)
        result = result.model_copy(update={"stale": stale or result.stale})
        # Some tools have no live version yet and still answer from saved files. In a live run, mark their
        # results so the roadmap can say which parts are not real data.
        if mode == "live" and result.mock and "mock_data_in_live_run" not in result.flags:
            result = result.model_copy(update={"flags": [*result.flags, "mock_data_in_live_run"]})

        check3 = run_check3(result, freshness_kind=kind)
        seq = _append_check_event(run, seq, "check3", check3)
        if not check3.get("passed"):
            limits.record_failed_tool_attempt(tool_name)
            return _close_run(
                run,
                seq=seq,
                status=Run.Status.FAILED,
                output={"error": check3.get("message"), "flags": check3.get("flags", [])},
                t0=t0,
                tool_call_count=limits.tool_call_count,
            )

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
