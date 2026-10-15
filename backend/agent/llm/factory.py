"""
Pick the LLM implementation from LLM_PROVIDER in settings or the environment.
"""

from __future__ import annotations

import os

from django.conf import settings

from agent.llm.anthropic_client import AnthropicLLM
from agent.llm.base import LLMClient
from agent.llm.scripted import ScriptedLLM


def get_llm_client(provider: str | None, *, fixture_case: str) -> LLMClient:
    """
    Return scripted or anthropic client.

    provider overrides settings when run_case passes --llm.
    """
    name = (provider or getattr(settings, "LLM_PROVIDER", os.environ.get("LLM_PROVIDER", "anthropic"))).strip().lower()
    if name == "scripted":
        return ScriptedLLM(fixture_case)
    if name == "anthropic":
        return AnthropicLLM()
    raise ValueError(f"Unknown LLM_PROVIDER {name!r}; use anthropic or scripted.")
