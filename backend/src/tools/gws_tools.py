"""Agno tool wrappers for Google Workspace (gws) skills."""

import json

from agno.tools import tool

from src.skills.gws.sheet_writer import append_lead_to_sheet
from src.skills.gws.sheet_reader import read_sheet_leads as _read_sheet_leads
from src.skills.gws.email_sender import send_email as _send_email


@tool
def write_lead_to_sheet(
    name: str,
    role_title: str = "",
    whatsapp: str = "",
    phone: str = "",
    details: str = "",
    email: str = "",
    company_name: str = "",
    website: str = "",
    source: str = "",
) -> str:
    """Append a verified lead row to the Google Sheet.

    Columns: Name, Role/Title, WhatsApp, Phone, Details, Email, Company Name, Website, Source.

    Args:
        name: Lead name.
        role_title: Role or title.
        whatsapp: WhatsApp number.
        phone: Phone number.
        details: Additional details.
        email: Email address.
        company_name: Company name.
        website: Website URL.
        source: Source information.

    Returns:
        JSON result with success status and any error details.
    """
    result = append_lead_to_sheet(
        name=name,
        role_title=role_title,
        whatsapp=whatsapp,
        phone=phone,
        details=details,
        email=email,
        company_name=company_name,
        website=website,
        source=source,
    )
    return json.dumps({
        "success": result.success,
        "error": result.error,
        "data": result.data,
    })


@tool
def read_sheet_leads(range_: str = "Sheet1!A:I") -> str:
    """Read existing leads from the Google Sheet for deduplication checking.

    Args:
        range_: Sheet range to read (defaults to Sheet1!A:I).

    Returns:
        JSON result with sheet values or error details.
    """
    result = _read_sheet_leads(range_=range_)
    return json.dumps({
        "success": result.success,
        "error": result.error,
        "data": result.data,
    })


@tool
def send_outreach_email(to: str, subject: str, body: str) -> str:
    """Send an approved outreach email via Gmail.

    Only call this for emails that have been reviewed and approved.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body text.

    Returns:
        JSON result with success status, provider message ID, or error.
    """
    result = _send_email(to=to, subject=subject, body=body)
    return json.dumps({
        "success": result.success,
        "error": result.error,
        "data": result.data,
    })
