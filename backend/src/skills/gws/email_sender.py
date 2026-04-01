"""Email sender skill — send approved outreach via gws gmail."""
from src.skills.gws.subprocess_runner import run_gws_command, GWSResult


def send_email(to: str, subject: str, body: str) -> GWSResult:
    """Send an approved outreach email via gws gmail.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body text

    Returns:
        GWSResult with provider message ID on success
    """
    return run_gws_command([
        "gmail", "+send",
        "--to", to,
        "--subject", subject,
        "--body", body,
    ])


SKILL_METADATA = {
    "id": "email-sender",
    "version": "1.0.0",
    "description": "Send approved outreach via gws gmail",
    "wraps": "gws gmail +send",
}
