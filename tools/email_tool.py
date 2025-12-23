"""
# ================================================================
#   ____   ___   ____      _
#  / ___| / _ \ |  _ \    / \
# | |    | | | || |_) |  / _ \
# | |___ | |_| ||  _ <  / ___ \
#  \____| \___/ |_| \_\/_/   \_\
#
# C.O.R.A Email Module
# ================================================================
# Version: 2.3.0
# Unity AI Lab
# Website: https://www.unityailab.com
# GitHub: https://github.com/Unity-Lab-AI
# Contact: unityailabcontact@gmail.com
# Creators: Hackall360, Sponge, GFourteen
# ================================================================
#
# Send emails via SMTP (Gmail, Outlook, etc.)
# Requires email credentials in config.
#
# ================================================================
"""

import smtplib
import json
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


# Default config location
CONFIG_DIR = Path(__file__).parent.parent / 'config'
EMAIL_CONFIG_FILE = CONFIG_DIR / 'email_config.json'


def load_email_config() -> dict:
    """Load email configuration from file.

    Config file should contain:
    {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 465,
        "email_address": "your@email.com",
        "app_password": "your-app-password"
    }
    """
    if EMAIL_CONFIG_FILE.exists():
        try:
            with open(EMAIL_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def send_email(
    to: str,
    subject: str,
    body: str,
    html: bool = False,
    config: dict = None
) -> dict:
    """
    Send an email via SMTP.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body (plain text or HTML)
        html: If True, body is treated as HTML
        config: Optional config dict with smtp_server, smtp_port, email_address, app_password

    Returns:
        dict with 'success', 'message', and optional 'error'
    """
    if config is None:
        config = load_email_config()

    # Validate config
    required = ['smtp_server', 'smtp_port', 'email_address', 'app_password']
    missing = [k for k in required if not config.get(k)]

    if missing:
        return {
            'success': False,
            'error': f'Missing email config: {", ".join(missing)}',
            'hint': f'Create {EMAIL_CONFIG_FILE} with smtp_server, smtp_port, email_address, app_password'
        }

    try:
        smtp_server = config['smtp_server']
        smtp_port = int(config['smtp_port'])
        sender = config['email_address']
        password = config['app_password']

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to

        if html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))

        # Send via SMTP SSL
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender, password)
            server.sendmail(sender, to, msg.as_string())

        return {
            'success': True,
            'message': f'Email sent to {to}',
            'subject': subject
        }

    except smtplib.SMTPAuthenticationError:
        return {
            'success': False,
            'error': 'SMTP authentication failed. Check email_address and app_password.'
        }
    except smtplib.SMTPException as e:
        return {
            'success': False,
            'error': f'SMTP error: {e}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Email error: {e}'
        }


def create_email_config(
    email_address: str,
    app_password: str,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 465
) -> dict:
    """
    Create email configuration file.

    Args:
        email_address: Your email address
        app_password: App-specific password (NOT your regular password)
        smtp_server: SMTP server (default: Gmail)
        smtp_port: SMTP port (default: 465 for SSL)

    Returns:
        dict with success status
    """
    config = {
        'smtp_server': smtp_server,
        'smtp_port': smtp_port,
        'email_address': email_address,
        'app_password': app_password
    }

    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(EMAIL_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return {'success': True, 'message': f'Config saved to {EMAIL_CONFIG_FILE}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# CLI-friendly wrapper
def email(to: str, subject: str, body: str) -> str:
    """Send an email. Returns status message."""
    result = send_email(to, subject, body)
    if result['success']:
        return f"[+] {result['message']}"
    else:
        return f"[!] {result['error']}"


# Module test
if __name__ == "__main__":
    print("=" * 50)
    print("  C.O.R.A Email Module Test")
    print("  Unity AI Lab")
    print("=" * 50)

    config = load_email_config()
    if config:
        print(f"[+] Config loaded from {EMAIL_CONFIG_FILE}")
        print(f"    SMTP: {config.get('smtp_server')}:{config.get('smtp_port')}")
        print(f"    From: {config.get('email_address')}")
    else:
        print(f"[!] No config found at {EMAIL_CONFIG_FILE}")
        print("    Create config with create_email_config() or manually")
