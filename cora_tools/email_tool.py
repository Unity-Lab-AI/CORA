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
# Version: 1.0.0
# Unity AI Lab
# Website: https://www.unityailab.com
# GitHub: https://github.com/Unity-Lab-AI
# Contact: unityailabcontact@gmail.com
# Creators: Hackall360, Sponge, GFourteen
# ================================================================
#
# Opens default email app (Outlook, etc.) for sending emails.
# Supports contact lookup by name.
#
# ================================================================
"""

import os
import json
import subprocess
import webbrowser
from pathlib import Path
from urllib.parse import quote
from typing import Optional, Dict, Any

# Config paths
PROJECT_DIR = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_DIR / 'config'
DATA_DIR = PROJECT_DIR / 'data'
CONTACTS_FILE = DATA_DIR / 'contacts.json'

# Load user name from settings
def get_user_name() -> str:
    """Get user's name from settings."""
    settings_file = CONFIG_DIR / 'settings.json'
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                return settings.get('user_name', 'Your friend')
        except:
            pass
    return 'Your friend'


def load_contacts() -> Dict[str, str]:
    """Load contacts from file.

    Returns dict of name -> email address
    """
    if CONTACTS_FILE.exists():
        try:
            with open(CONTACTS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_contacts(contacts: Dict[str, str]) -> bool:
    """Save contacts to file."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONTACTS_FILE, 'w') as f:
            json.dump(contacts, f, indent=2)
        return True
    except:
        return False


def add_contact(name: str, email: str) -> Dict[str, Any]:
    """Add a contact to the address book.

    Args:
        name: Contact name (e.g., "Karen", "Mom", "Boss")
        email: Email address

    Returns:
        dict with success status
    """
    contacts = load_contacts()
    name_lower = name.lower().strip()
    contacts[name_lower] = email.strip()

    if save_contacts(contacts):
        return {
            'success': True,
            'message': f'Added {name} ({email}) to contacts'
        }
    return {
        'success': False,
        'error': 'Failed to save contact'
    }


def get_contact_email(name: str) -> Optional[str]:
    """Look up email address by contact name.

    Args:
        name: Contact name to look up

    Returns:
        Email address or None if not found
    """
    contacts = load_contacts()
    name_lower = name.lower().strip()

    # Exact match
    if name_lower in contacts:
        return contacts[name_lower]

    # Partial match
    for contact_name, email in contacts.items():
        if name_lower in contact_name or contact_name in name_lower:
            return email

    return None


def list_contacts() -> Dict[str, Any]:
    """List all saved contacts."""
    contacts = load_contacts()
    if contacts:
        return {
            'success': True,
            'contacts': contacts,
            'count': len(contacts)
        }
    return {
        'success': True,
        'contacts': {},
        'count': 0,
        'message': 'No contacts saved. Add contacts with: add_contact("name", "email@example.com")'
    }


def send_email(
    to: str,
    message: str,
    subject: str = None
) -> Dict[str, Any]:
    """
    Open default email app with pre-filled email.

    Args:
        to: Recipient name or email address
        message: Message body
        subject: Optional subject (auto-generated if not provided)

    Returns:
        dict with success status
    """
    user_name = get_user_name()

    # Check if 'to' is a name (look up in contacts)
    recipient_email = to
    recipient_name = to

    if '@' not in to:
        # It's a name, look up email
        email_lookup = get_contact_email(to)
        if email_lookup:
            recipient_email = email_lookup
            recipient_name = to.title()
        else:
            return {
                'success': False,
                'error': f'No email address found for "{to}"',
                'hint': f'Add contact with: add_contact("{to}", "email@example.com")'
            }

    # Auto-generate subject if not provided
    if not subject:
        subject = f"Message from {user_name} via CORA"

    # Format the message body
    full_body = f'{user_name} says:\n\n"{message}"\n\n---\nSent via C.O.R.A - Cognitive Operations & Reasoning Assistant'

    # Try Windows mailto with Outlook first
    try:
        # Build mailto URL
        mailto_url = f"mailto:{quote(recipient_email)}"
        mailto_url += f"?subject={quote(subject)}"
        mailto_url += f"&body={quote(full_body)}"

        # Open default mail app
        webbrowser.open(mailto_url)

        return {
            'success': True,
            'message': f'Opening email to {recipient_name} ({recipient_email})',
            'to': recipient_email,
            'subject': subject
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to open email app: {e}'
        }


def draft_email(
    to: str,
    message: str,
    subject: str = None
) -> Dict[str, Any]:
    """Alias for send_email - opens email app with draft."""
    return send_email(to, message, subject)


def read_emails() -> Dict[str, Any]:
    """Open default email app to check emails."""
    try:
        # Try to open Outlook specifically on Windows
        if os.name == 'nt':
            try:
                # Try to open Outlook inbox
                subprocess.Popen(
                    ['start', 'outlook', '/select', 'outlook:inbox'],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return {
                    'success': True,
                    'message': 'Opening Outlook inbox'
                }
            except:
                pass

        # Fallback: open default mail app
        webbrowser.open('mailto:')
        return {
            'success': True,
            'message': 'Opening email app'
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to open email app: {e}'
        }


def check_email() -> Dict[str, Any]:
    """Alias for read_emails."""
    return read_emails()


# ============ CLI-Friendly Wrappers ============

def email_send(to: str, message: str, subject: str = None) -> str:
    """Send an email (opens default mail app)."""
    result = send_email(to, message, subject)
    if result['success']:
        return f"[+] {result['message']}"
    else:
        error = result.get('error', 'Unknown error')
        hint = result.get('hint', '')
        return f"[!] {error}" + (f"\n    {hint}" if hint else "")


def email_read() -> str:
    """Open email app to check emails."""
    result = read_emails()
    if result['success']:
        return f"[+] {result['message']}"
    return f"[!] {result['error']}"


def email_draft(to: str, message: str, subject: str = None) -> str:
    """Create email draft (opens default mail app)."""
    return email_send(to, message, subject)


# ============ Voice Command Helpers ============

def parse_email_command(text: str) -> Dict[str, Any]:
    """
    Parse natural language email command.

    Examples:
        "send email to karen saying hi"
        "email mom and say I'll be late"
        "send a message to john@example.com saying thanks"

    Returns:
        dict with 'to', 'message', or 'error'
    """
    text = text.lower().strip()

    # Common patterns
    patterns = [
        # "send email to X saying Y"
        ('send email to ', ' saying '),
        ('send an email to ', ' saying '),
        ('email ', ' saying '),
        ('email ', ' and say '),
        ('send message to ', ' saying '),
        ('send a message to ', ' saying '),
        # "tell X that Y"
        ('tell ', ' that '),
        ('message ', ' that '),
    ]

    for start_pattern, mid_pattern in patterns:
        if start_pattern in text and mid_pattern in text:
            try:
                start_idx = text.index(start_pattern) + len(start_pattern)
                mid_idx = text.index(mid_pattern, start_idx)

                recipient = text[start_idx:mid_idx].strip()
                message = text[mid_idx + len(mid_pattern):].strip()

                if recipient and message:
                    return {
                        'success': True,
                        'to': recipient,
                        'message': message
                    }
            except:
                continue

    return {
        'success': False,
        'error': 'Could not parse email command',
        'hint': 'Try: "send email to [name] saying [message]"'
    }


# Module test
if __name__ == "__main__":
    print("=" * 50)
    print("  C.O.R.A Email Module Test")
    print("  Unity AI Lab")
    print("=" * 50)

    # Test contact management
    print("\n[Testing Contacts]")
    contacts = load_contacts()
    print(f"  Loaded {len(contacts)} contacts")

    # Test parsing
    print("\n[Testing Command Parsing]")
    test_commands = [
        "send email to karen saying hi how are you",
        "email mom saying I'll be home late",
        "send a message to john@test.com saying thanks for the help"
    ]

    for cmd in test_commands:
        result = parse_email_command(cmd)
        if result['success']:
            print(f"  ✓ '{cmd[:40]}...'")
            print(f"    To: {result['to']}, Message: {result['message'][:30]}...")
        else:
            print(f"  ✗ '{cmd[:40]}...' - {result['error']}")
