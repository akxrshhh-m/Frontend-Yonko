"""
Participant Model
"""
from dataclasses import dataclass, field
from utils.id_generator import generate_participant_id, timestamp


@dataclass
class Participant:
    """Represents a participant/guest."""
    
    name: str
    email: str
    id: str = field(default_factory=generate_participant_id)
    phone: str = ""
    affiliation: str = "Independent"  # e.g., "Straw Hat Pirates", "World Government"
    created_at: str = field(default_factory=timestamp)
    
    def to_dict(self) -> dict:
        """Convert participant to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "affiliation": self.affiliation,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Participant":
        """Create Participant from dictionary."""
        return cls(
            id=data.get("id", generate_participant_id()),
            name=data["name"],
            email=data["email"],
            phone=data.get("phone", ""),
            affiliation=data.get("affiliation", "Independent"),
            created_at=data.get("created_at", timestamp()),
        )