"""Sheet reader skill — read existing sheet data."""
import json

from src.config import settings
from src.skills.gws.subprocess_runner import run_gws_command, GWSResult


def read_sheet_leads(
    sheet_id: str | None = None,
    range_: str = "Sheet1!A:I",
) -> GWSResult:
    """Read existing leads from the Google Sheet for dedup checking.

    Args:
        sheet_id: Override sheet ID (defaults to config)
        range_: Sheet range to read (defaults to Sheet1!A:I)

    Returns:
        GWSResult with sheet values on success
    """
    sid = sheet_id or settings.google_sheet_id
    if not sid:
        return GWSResult(
            success=False, data=None, error="No sheet ID configured", raw_output=""
        )

    return run_gws_command([
        "sheets", "spreadsheets.values", "get",
        "--params", json.dumps({
            "spreadsheetId": sid,
            "range": range_,
        }),
    ])


SKILL_METADATA = {
    "id": "sheet-reader",
    "version": "1.0.0",
    "description": "Read existing sheet data for dedup",
    "wraps": "gws sheets spreadsheets.values get",
}
