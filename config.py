"""
Configuration constants for Gran Tesoro RSVP System
"""

# Offer expiration time in seconds (for waitlisted participants)
OFFER_EXPIRATION_SECONDS = 300  # 5 minutes

# Default event capacity
DEFAULT_CAPACITY = 50

# Maximum waitlist size per event (0 = unlimited)
MAX_WAITLIST_SIZE = 0

# Theme Configuration
THEME = {
    "app_name": "Gran Tesoro VIP Gala & Reverie Summit RSVP",
    "currency": "Belly (฿)",
    "organizer_title": "Gild Tesoro's Golden Entertainment Division",
    "waitlist_name": "Silver Room Queue",
    "confirmed_name": "VIP Gold Room Guest",
    "offer_name": "Golden Den Den Mushi Invitation",
}

# Registration statuses
class RegistrationStatus:
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    WAITLISTED = "WAITLISTED"

# Offer statuses
class OfferStatus:
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"

# Event statuses
class EventStatus:
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    FULL = "FULL"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"