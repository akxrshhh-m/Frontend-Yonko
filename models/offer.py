"""
Seat Offer Model - Golden Den Den Mushi Invitation
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from config import OfferStatus, OFFER_EXPIRATION_SECONDS
from utils.id_generator import generate_offer_id, timestamp


@dataclass
class SeatOffer:
    """Represents a timed seat offer to a waitlisted participant."""
    
    event_id: str
    participant_id: str
    waitlist_entry_id: str
    id: str = field(default_factory=generate_offer_id)
    status: str = field(default=OfferStatus.PENDING)
    created_at: str = field(default_factory=timestamp)
    expires_at: str = ""
    responded_at: str = None
    expiration_seconds: int = OFFER_EXPIRATION_SECONDS
    
    def __post_init__(self):
        if not self.expires_at:
            expiry = datetime.utcnow() + timedelta(seconds=self.expiration_seconds)
            self.expires_at = expiry.isoformat() + "Z"
    
    @property
    def is_expired(self) -> bool:
        """Check if the offer has expired."""
        if self.status != OfferStatus.PENDING:
            return False
        try:
            expiry_dt = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            now = datetime.utcnow().replace(tzinfo=expiry_dt.tzinfo)
            return now > expiry_dt
        except (ValueError, AttributeError):
            return False
    
    @property
    def time_remaining_seconds(self) -> int:
        """Get remaining time in seconds."""
        if self.status != OfferStatus.PENDING:
            return 0
        try:
            expiry_dt = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            now = datetime.utcnow().replace(tzinfo=expiry_dt.tzinfo)
            remaining = (expiry_dt - now).total_seconds()
            return max(0, int(remaining))
        except (ValueError, AttributeError):
            return 0
    
    def to_dict(self) -> dict:
        """Convert offer to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "participant_id": self.participant_id,
            "waitlist_entry_id": self.waitlist_entry_id,
            "status": self.status,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "responded_at": self.responded_at,
            "time_remaining_seconds": self.time_remaining_seconds,
            "is_expired": self.is_expired,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SeatOffer":
        """Create SeatOffer from dictionary."""
        return cls(
            id=data.get("id", generate_offer_id()),
            event_id=data["event_id"],
            participant_id=data["participant_id"],
            waitlist_entry_id=data["waitlist_entry_id"],
            status=data.get("status", OfferStatus.PENDING),
            created_at=data.get("created_at", timestamp()),
            expires_at=data.get("expires_at", ""),
            responded_at=data.get("responded_at"),
            expiration_seconds=data.get("expiration_seconds", OFFER_EXPIRATION_SECONDS),
        )