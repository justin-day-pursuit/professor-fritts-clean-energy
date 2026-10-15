"""Tests for v4 cache: versioning, rollback, safe-change rule, approved sources."""

import pytest
from tools.approved_sources import is_approved_source
from tools.cache import DjangoCacheBackend


class TestApprovedSources:
    def test_irs_is_approved(self):
        assert is_approved_source("https://www.irs.gov/credits-deductions/elective-pay")

    def test_nyserda_is_approved(self):
        assert is_approved_source("https://www.nyserda.ny.gov/programs")

    def test_coned_is_approved(self):
        assert is_approved_source("https://www.coned.com/en/save-money/using-solar-energy-at-home")

    def test_example_test_fixture_is_approved(self):
        assert is_approved_source("https://example.test/fictional/case2/incentives")

    def test_random_blog_is_not_approved(self):
        assert not is_approved_source("https://solarreviews.com/best-panels")

    def test_empty_url_is_not_approved(self):
        assert not is_approved_source("")

    def test_user_input_url_is_not_approved(self):
        assert not is_approved_source("session://profile")

    def test_calculate_internal_url_is_not_approved(self):
        assert not is_approved_source("internal://calculate")


@pytest.mark.django_db
class TestDjangoCacheBackend:
    def test_put_and_get(self):
        cache = DjangoCacheBackend()
        cache.put(
            "test:record",
            {"status": "open"},
            source_url="https://nyserda.ny.gov/test",
            retrieved_at="2026-10-15T12:00:00Z",
        )
        result = cache.get("test:record")
        assert result == {"status": "open"}

    def test_versions_are_append_only(self):
        cache = DjangoCacheBackend()
        cache.put(
            "test:v",
            {"status": "open"},
            source_url="https://nyserda.ny.gov/test",
            retrieved_at="2026-10-01T12:00:00Z",
        )
        cache.put(
            "test:v",
            {"status": "closed"},
            source_url="https://nyserda.ny.gov/test",
            retrieved_at="2026-10-15T12:00:00Z",
        )
        versions = cache.versions("test:v")
        assert len(versions) == 2
        assert versions[0]["data"]["status"] == "open"
        assert versions[1]["data"]["status"] == "closed"

    def test_rollback_restores_previous(self):
        cache = DjangoCacheBackend()
        cache.put(
            "test:rb",
            {"status": "open"},
            source_url="https://nyserda.ny.gov/test",
            retrieved_at="2026-10-01T12:00:00Z",
        )
        cache.put(
            "test:rb",
            {"status": "closed"},
            source_url="https://nyserda.ny.gov/test",
            retrieved_at="2026-10-15T12:00:00Z",
        )
        assert cache.get("test:rb") == {"status": "closed"}
        restored = cache.rollback("test:rb")
        assert restored is not None
        assert restored["data"]["status"] == "open"
        assert cache.get("test:rb") == {"status": "open"}

    def test_safe_change_cautious_auto_saves(self):
        """open→closed is cautious and saves without pending."""
        cache = DjangoCacheBackend()
        cache.put(
            "test:sc",
            {"status": "open"},
            source_url="https://nyserda.ny.gov/test",
            retrieved_at="2026-10-01T12:00:00Z",
        )
        result = cache.put(
            "test:sc",
            {"status": "closed"},
            source_url="https://nyserda.ny.gov/test",
            retrieved_at="2026-10-15T12:00:00Z",
        )
        assert result["changed"] is True
        assert result["pending"] is False

    def test_safe_change_favorable_saves_as_pending(self):
        """closed→open is favorable and saves as pending."""
        cache = DjangoCacheBackend()
        cache.put(
            "test:sf",
            {"status": "closed"},
            source_url="https://nyserda.ny.gov/test",
            retrieved_at="2026-10-01T12:00:00Z",
        )
        result = cache.put(
            "test:sf",
            {"status": "open"},
            source_url="https://nyserda.ny.gov/test",
            retrieved_at="2026-10-15T12:00:00Z",
        )
        assert result["changed"] is True
        assert result["pending"] is True
        # Pending records are not returned by get()
        assert cache.get("test:sf") == {"status": "closed"}

    def test_confirm_pending(self):
        cache = DjangoCacheBackend()
        cache.put(
            "test:cp",
            {"status": "closed"},
            source_url="https://nyserda.ny.gov/test",
            retrieved_at="2026-10-01T12:00:00Z",
        )
        result = cache.put(
            "test:cp",
            {"status": "open"},
            source_url="https://nyserda.ny.gov/test",
            retrieved_at="2026-10-15T12:00:00Z",
        )
        assert result["pending"] is True
        cache.confirm_pending("test:cp", result["version"])
        assert cache.get("test:cp") == {"status": "open"}


@pytest.mark.django_db
class TestUpsertTool:
    def test_rejects_unapproved_source(self):
        from tools.upsert_cache import upsert_reference_cache

        result = upsert_reference_cache(
            "test:bad",
            {"status": "open"},
            source_url="https://solarreviews.com/scam",
        )
        assert "rejected_unapproved_source" in result.flags

    def test_rejects_missing_source(self):
        from tools.upsert_cache import upsert_reference_cache

        result = upsert_reference_cache("test:no-src", {"status": "open"})
        assert "rejected_no_source" in result.flags

    def test_accepts_approved_source(self):
        from tools.upsert_cache import upsert_reference_cache

        result = upsert_reference_cache(
            "test:good",
            {"status": "open"},
            source_url="https://nyserda.ny.gov/programs",
            retrieved_at="2026-10-15T12:00:00Z",
        )
        assert result.data.get("version") == 1
        assert "rejected_unapproved_source" not in result.flags
        assert "rejected_no_source" not in result.flags
