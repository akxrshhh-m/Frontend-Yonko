"""
Waitlist Entry Model
"""
from dataclasses import dataclass, field
from utils.id_generator import generate_waitlist_id, timestamp


@dataclass
class WaitlistEntry:
    """Represents an entry in the waitlist (Silver Room Queue)."""
    
    event_id: str
    participant_id: str
    position: int
    id: str = field(default_factory=generate_waitlist_id)
    rank_title: str = "East Blue Rookie Priority"
    added_at: str = field(default_factory=timestamp)
    is_active: bool = True  # False when promoted or removed
    
    def to_dict(self) -> dict:
        """Convert waitlist entry to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "participant_id": self.participant_id,
            "position": self.position,
            "rank_title": self.rank_title,
            "added_at": self.added_at,
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "WaitlistEntry":
        """Create WaitlistEntry from dictionary."""
        return cls(
            id=data.get("id", generate_waitlist_id()),
            event_id=data["event_id"],
            participant_id=data["participant_id"],
            position=data["position"],
            rank_title=data.get("rank_title", "East Blue Rookie Priority"),
            added_at=data.get("added_at", timestamp()),
            is_active=data.get("is_active", True),
        )