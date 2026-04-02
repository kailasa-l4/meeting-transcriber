"""Rate limiting and politeness controls for discovery skills."""
import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    min_delay_seconds: float = 1.0  # Minimum delay between requests to same domain
    max_concurrent_per_domain: int = 2
    max_errors_before_circuit_break: int = 5
    circuit_break_duration_seconds: float = 300.0  # 5 minutes


@dataclass
class DomainState:
    """Tracks state for a single domain."""
    last_request_time: float = 0.0
    active_requests: int = 0
    error_count: int = 0
    circuit_broken_until: float = 0.0


class RateLimiter:
    """Rate limiter with per-domain tracking and circuit breaker."""

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._domains: dict[str, DomainState] = defaultdict(DomainState)

    def can_request(self, domain: str) -> bool:
        """Check if a request to this domain is allowed."""
        state = self._domains[domain]
        now = time.time()

        # Circuit breaker check
        if state.circuit_broken_until > now:
            logger.warning(f"Circuit broken for {domain}, skipping")
            return False

        # Concurrency check
        if state.active_requests >= self.config.max_concurrent_per_domain:
            return False

        # Rate limit check
        if now - state.last_request_time < self.config.min_delay_seconds:
            return False

        return True

    def acquire(self, domain: str) -> bool:
        """Acquire a request slot for a domain. Returns False if not allowed."""
        if not self.can_request(domain):
            return False
        state = self._domains[domain]
        state.active_requests += 1
        state.last_request_time = time.time()
        return True

    def release(self, domain: str, success: bool = True):
        """Release a request slot and record outcome."""
        state = self._domains[domain]
        state.active_requests = max(0, state.active_requests - 1)

        if not success:
            state.error_count += 1
            if state.error_count >= self.config.max_errors_before_circuit_break:
                state.circuit_broken_until = time.time() + self.config.circuit_break_duration_seconds
                logger.warning(f"Circuit breaker tripped for {domain}")
        else:
            state.error_count = max(0, state.error_count - 1)  # Decay errors on success

    def wait_for_slot(self, domain: str, timeout: float = 30.0) -> bool:
        """Wait until a request slot is available. Returns False on timeout."""
        start = time.time()
        while time.time() - start < timeout:
            if self.acquire(domain):
                return True
            time.sleep(0.1)
        return False

    def get_stats(self) -> dict:
        """Get current rate limiter statistics."""
        now = time.time()
        return {
            domain: {
                "active_requests": state.active_requests,
                "error_count": state.error_count,
                "circuit_broken": state.circuit_broken_until > now,
            }
            for domain, state in self._domains.items()
        }


# Global rate limiter instance
discovery_rate_limiter = RateLimiter()
