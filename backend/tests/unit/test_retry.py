"""Tests for retry decorator."""
import pytest
from src.utils.retry import retry


class TestRetry:
    def test_succeeds_first_try(self):
        call_count = 0

        @retry(max_attempts=3)
        def always_works():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert always_works() == "ok"
        assert call_count == 1

    def test_retries_on_failure(self):
        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        assert fails_twice() == "ok"
        assert call_count == 3

    def test_exhausts_retries(self):
        @retry(max_attempts=2, delay=0.01)
        def always_fails():
            raise ValueError("always")

        with pytest.raises(ValueError, match="always"):
            always_fails()

    def test_only_retries_specified_exceptions(self):
        @retry(max_attempts=3, delay=0.01, exceptions=(TypeError,))
        def raises_value_error():
            raise ValueError("wrong type")

        with pytest.raises(ValueError):
            raises_value_error()
