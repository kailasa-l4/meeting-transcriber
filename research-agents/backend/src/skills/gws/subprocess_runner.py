"""Centralized gws CLI subprocess runner."""
import json
import subprocess
from dataclasses import dataclass


@dataclass
class GWSResult:
    success: bool
    data: dict | list | None
    error: str | None
    raw_output: str


def run_gws_command(args: list[str], timeout: int = 30) -> GWSResult:
    """Execute a gws CLI command and parse JSON output.

    Args:
        args: Command arguments (e.g., ["sheets", "spreadsheets.values", "append", ...])
        timeout: Command timeout in seconds

    Returns:
        GWSResult with parsed JSON or error
    """
    cmd = ["gws"] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return GWSResult(
                success=False,
                data=None,
                error=result.stderr.strip() or f"Exit code {result.returncode}",
                raw_output=result.stdout,
            )
        try:
            data = json.loads(result.stdout) if result.stdout.strip() else None
        except json.JSONDecodeError:
            data = None
        return GWSResult(success=True, data=data, error=None, raw_output=result.stdout)
    except subprocess.TimeoutExpired:
        return GWSResult(success=False, data=None, error="Command timed out", raw_output="")
    except FileNotFoundError:
        return GWSResult(success=False, data=None, error="gws CLI not found", raw_output="")


SKILL_METADATA = {
    "id": "gws-subprocess-runner",
    "version": "1.0.0",
    "description": "Centralized gws CLI execution",
}
