"""
Health check route — confirms the combined FastAPI + Django process is running.
"""

from django import get_version
from django.conf import settings
from fastapi import APIRouter

from api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return ok status plus tool/LLM modes and Django version for ops and tests."""
    return HealthResponse(
        status="ok",
        tool_mode=getattr(settings, "TOOL_MODE", "mock"),
        llm_provider=getattr(settings, "LLM_PROVIDER", "anthropic"),
        django_version=get_version(),
    )
