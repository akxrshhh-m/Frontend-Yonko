"""
Input validation utilities
"""
from datetime import datetime
from typing import Optional


class ValidationError(Exception):
    """Custom validation error."""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_required_string(value: str, field_name: str) -> str:
    """Validate that a string is not empty."""
    if not value or not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} is required and cannot be empty.", field_name)
    return value.strip()


def validate_positive_integer(value, field_name: str) -> int:
    """Validate that a value is a positive integer."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid integer.", field_name)
    if value <= 0:
        raise ValidationError(f"{field_name} must be a positive integer.", field_name)
    return value


def validate_non_negative_integer(value, field_name: str) -> int:
    """Validate that a value is a non-negative integer."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid integer.", field_name)
    if value < 0:
        raise ValidationError(f"{field_name} cannot be negative.", field_name)
    return value


def validate_email(email: str) -> str:
    """Basic email validation."""
    email = validate_required_string(email, "Email")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValidationError("Invalid email format.", "email")
    return email.lower()


def validate_future_date(date_str: str, field_name: str = "Date") -> datetime:
    """Validate that a date string is in the future."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            raise ValidationError(
                f"{field_name} must be in ISO format (YYYY-MM-DDTHH:MM:SS) or 'YYYY-MM-DD HH:MM'.",
                field_name
            )
    return dt


def validate_capacity(capacity, current_registrations: int = 0) -> int:
    """Validate event capacity."""
    capacity = validate_positive_integer(capacity, "Capacity")
    if current_registrations > 0 and capacity < current_registrations:
        raise ValidationError(
            f"Capacity ({capacity}) cannot be less than current registrations ({current_registrations}).",
            "capacity"
        )
    return capacity