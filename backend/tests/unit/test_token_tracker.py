"""Tests for token tracking."""
from src.utils.token_tracker import track_token_usage, get_session_cost_summary


class TestTokenTracker:
    def test_track_updates_job(self, db_session, sample_country_job):
        track_token_usage(db_session, str(sample_country_job.id), 1000, "discovery")
        db_session.flush()
        assert sample_country_job.total_token_count == 1000
        assert sample_country_job.estimated_cost > 0

    def test_track_accumulates(self, db_session, sample_country_job):
        track_token_usage(db_session, str(sample_country_job.id), 1000, "discovery")
        track_token_usage(db_session, str(sample_country_job.id), 500, "verification")
        db_session.flush()
        assert sample_country_job.total_token_count == 1500

    def test_cost_summary(self, db_session, sample_country_job):
        track_token_usage(db_session, str(sample_country_job.id), 10000, "discovery")
        db_session.flush()
        summary = get_session_cost_summary(db_session, str(sample_country_job.id))
        assert summary["total_tokens"] == 10000
        assert summary["estimated_cost_usd"] > 0
        assert summary["country"] == "Ghana"
