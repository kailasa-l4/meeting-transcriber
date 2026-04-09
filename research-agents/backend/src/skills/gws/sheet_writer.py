"""Sheet writer skill — append leads to Google Sheet."""
import json

from src.config import settings
from src.skills.gws.subprocess_runner import run_gws_command, GWSResult


def append_lead_to_sheet(
    name: str,
    role_title: str = "",
    whatsapp: str = "",
    phone: str = "",
    details: str = "",
    email: str = "",
    company_name: str = "",
    website: str = "",
    source: str = "",
    sheet_id: str | None = None,
) -> GWSResult:
    """Append a lead row to the Google Sheet.

    Columns: Name, Role/Title, WhatsApp, Phone, Details, Email, Company Name, Website, Source

    Args:
        name: Lead name
        role_title: Role or title
        whatsapp: WhatsApp number
        phone: Phone number
        details: Additional details
        email: Email address
        company_name: Company name
        website: Website URL
        source: Source information
        sheet_id: Override sheet ID (defaults to config)

    Returns:
        GWSResult with append response on success
    """
    sid = sheet_id or settings.google_sheet_id
    if not sid:
        return GWSResult(
            success=False, data=None, error="No sheet ID configured", raw_output=""
        )

    values = json.dumps({
        "values": [[name, role_title, whatsapp, phone, details, email, company_name, website, source]]
    })

    return run_gws_command([
        "sheets", "spreadsheets.values", "append",
        "--params", json.dumps({
            "spreadsheetId": sid,
            "range": "Sheet1!A:I",
            "valueInputOption": "USER_ENTERED",
        }),
        "--json", values,
    ])


SKILL_METADATA = {
    "id": "sheet-writer",
    "version": "1.0.0",
    "description": "Append leads to Google Sheet",
    "wraps": "gws sheets spreadsheets.values append",
}
