"""Tests for rate limiter."""
from src.utils.rate_limiter import RateLimiter, RateLimitConfig


class TestRateLimiter:
    def test_allows_first_request(self):
        rl = RateLimiter(RateLimitConfig(min_delay_seconds=0))
        assert rl.acquire("example.com") is True

    def test_blocks_rapid_requests(self):
        rl = RateLimiter(RateLimitConfig(min_delay_seconds=10))
        assert rl.acquire("example.com") is True
        assert rl.can_request("example.com") is False

    def test_respects_max_concurrent(self):
        rl = RateLimiter(RateLimitConfig(min_delay_seconds=0, max_concurrent_per_domain=1))
        assert rl.acquire("example.com") is True
        assert rl.can_request("example.com") is False
        rl.release("example.com")
        assert rl.can_request("example.com") is True

    def test_circuit_breaker(self):
        rl = RateLimiter(RateLimitConfig(
            min_delay_seconds=0, max_errors_before_circuit_break=2, circuit_break_duration_seconds=100
        ))
        rl.acquire("bad.com")
        rl.release("bad.com", success=False)
        rl.acquire("bad.com")
        rl.release("bad.com", success=False)
        assert rl.can_request("bad.com") is False  # Circuit broken

    def test_independent_domains(self):
        rl = RateLimiter(RateLimitConfig(min_delay_seconds=0))
        assert rl.acquire("a.com") is True
        assert rl.acquire("b.com") is True

    def test_get_stats(self):
        rl = RateLimiter(RateLimitConfig(min_delay_seconds=0))
        rl.acquire("example.com")
        stats = rl.get_stats()
        assert "example.com" in stats
        assert stats["example.com"]["active_requests"] == 1
