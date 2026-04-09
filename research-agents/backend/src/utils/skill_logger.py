"""Skill invocation logging utility."""
import time
import uuid
import functools
import logging
from typing import Callable
from sqlalchemy.orm import Session
from src.db.models import SkillInvocationLog

logger = logging.getLogger(__name__)


def log_skill_invocation(
    skill_name: str,
    skill_version: str = "1.0.0",
    agent_name: str | None = None,
):
    """Decorator that logs skill invocations to the database.

    The decorated function must accept a `db` keyword argument (Session).
    If no db is provided, logging is skipped silently.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            db: Session | None = kwargs.get("db")
            start_time = time.time()
            input_summary = str(args[:3]) if args else str(kwargs)[:500]

            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)

                if db:
                    log_entry = SkillInvocationLog(
                        id=uuid.uuid4(),
                        country_job_id=kwargs.get("job_id"),
                        skill_name=skill_name,
                        skill_version=skill_version,
                        agent_name=agent_name,
                        input_summary=input_summary[:1000],
                        output_summary=str(result)[:1000],
                        duration_ms=duration_ms,
                        status="success",
                    )
                    db.add(log_entry)
                    try:
                        db.flush()
                    except Exception:
                        pass  # Don't fail the skill for logging errors

                return result
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)

                if db:
                    log_entry = SkillInvocationLog(
                        id=uuid.uuid4(),
                        country_job_id=kwargs.get("job_id"),
                        skill_name=skill_name,
                        skill_version=skill_version,
                        agent_name=agent_name,
                        input_summary=input_summary[:1000],
                        duration_ms=duration_ms,
                        status="error",
                        error_message=str(e)[:1000],
                    )
                    db.add(log_entry)
                    try:
                        db.flush()
                    except Exception:
                        pass

                raise
        return wrapper
    return decorator
