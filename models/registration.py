"""
Registration Model
"""
from dataclasses import dataclass, field
from config import RegistrationStatus
from utils.id_generator import generate_registration_id, timestamp


@dataclass
class Registration:
    """Represents a confirmed event registration."""
    
    event_id: str
    participant_id: str
    id: str = field(default_factory=generate_registration_id)
    status: str = field(default=RegistrationStatus.CONFIRMED)
    registration_number: int = 0  # Order of registration
    vip_tier: str = "General"
    registered_at: str = field(default_factory=timestamp)
    cancelled_at: str = None
    
    def to_dict(self) -> dict:
        """Convert registration to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "participant_id": self.participant_id,
            "status": self.status,
            "registration_number": self.registration_number,
            "vip_tier": self.vip_tier,
            "registered_at": self.registered_at,
            "cancelled_at": self.cancelled_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Registration":
        """Create Registration from dictionary."""
        return cls(
            id=data.get("id", generate_registration_id()),
            event_id=data["event_id"],
            participant_id=data["participant_id"],
            status=data.get("status", RegistrationStatus.CONFIRMED),
            registration_number=data.get("registration_number", 0),
            vip_tier=data.get("vip_tier", "General"),
            registered_at=data.get("registered_at", timestamp()),
            cancelled_at=data.get("cancelled_at"),
        )