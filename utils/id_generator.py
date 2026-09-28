"""
Unique ID generation utility
"""
import uuid
from datetime import datetime


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    short_uuid = uuid.uuid4().hex[:8].upper()
    if prefix:
        return f"{prefix}-{short_uuid}"
    return short_uuid


def generate_event_id() -> str:
    """Generate event ID themed as Gran Tesoro pass."""
    return generate_id("GT-EVT")


def generate_registration_id() -> str:
    """Generate registration ID."""
    return generate_id("GT-REG")


def generate_participant_id() -> str:
    """Generate participant ID themed as pirate bounty poster."""
    return generate_id("GT-PAR")


def generate_offer_id() -> str:
    """Generate offer ID themed as Den Den Mushi call."""
    return generate_id("GT-OFR")


def generate_waitlist_id() -> str:
    """Generate waitlist entry ID."""
    return generate_id("GT-WL")


def timestamp() -> str:
    """Generate current ISO timestamp."""
    return datetime.utcnow().isoformat() + "Z"