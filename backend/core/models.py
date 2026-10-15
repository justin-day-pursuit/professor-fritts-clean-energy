"""
Database models for planning sessions, uploaded files, chat, and agent runs.

These tables are what Django migrations manage; the agent harness and API talk to them
only through core.services (not raw ORM calls elsewhere).
"""

from __future__ import annotations

import uuid

from django.db import models


class Session(models.Model):
    """
    One building owner's planning conversation — intake profile and high-level status.

    The primary key is a UUID so the frontend can reference sessions without guessing ids.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    profile = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=64, default="active")
    # Which mock fixture folder to use when TOOL_MODE=mock (for example case1_queens_library).
    fixture_case = models.CharField(max_length=128, default="case1_queens_library")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        # Human label "Session <uuid>" for admin dropdowns and list links; change the f-string to show status or address instead.
        return f"Session {self.id}"


class Document(models.Model):
    """
    A file uploaded for a session (for example utility bills), stored on disk under .data/uploads/.
    """

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="documents")
    filename = models.CharField(max_length=512)
    content_type = models.CharField(max_length=128, blank=True, default="")
    size_bytes = models.PositiveBigIntegerField(default=0)
    stored_path = models.CharField(max_length=1024)
    parsed_summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        # Shows the uploaded filename in admin lists; edit return value if you want "filename (session)" instead.
        return self.filename


class Run(models.Model):
    """
    One agent execution for a session — tool mode, LLM provider, timing, and final output.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        NEEDS_INPUT = "needs_input", "Needs input"
        DONE = "done", "Done"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="runs")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.QUEUED)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    tool_mode = models.CharField(max_length=32, default="mock")
    llm_provider = models.CharField(max_length=32, default="anthropic")
    tool_call_count = models.PositiveIntegerField(default=0)
    elapsed_seconds = models.FloatField(null=True, blank=True)
    output = models.JSONField(default=dict, blank=True)
    flags = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        # Admin lists use "Run <id> (status)"; tweak the format here if operators need tool_mode in the label.
        return f"Run {self.pk} ({self.status})"


class Message(models.Model):
    """Chat line in a session — from the user, assistant, or system — optionally tied to one run."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    run = models.ForeignKey(
        Run,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        # Short preview "role: first 40 chars" in admin; lengthen the slice or drop role if clutter is a problem.
        return f"{self.role}: {self.content[:40]}"


class RunEvent(models.Model):
    """
    Ordered log entry for a run — checks, thinking steps, tool calls, and errors.

    The seq field keeps events in order; kind names match the harness diagram (check1, tool_call, etc.).
    """

    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="events")
    seq = models.PositiveIntegerField()
    kind = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["seq"]
        constraints = [
            models.UniqueConstraint(fields=["run", "seq"], name="unique_run_event_seq"),
        ]

    def __str__(self) -> str:
        # Labels each log line as "Event seq (kind) on run …" in admin; reorder words here if seq should come last.
        return f"Event {self.seq} ({self.kind}) on run {self.run_id}"
