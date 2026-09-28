"""
Event Model
"""
from dataclasses import dataclass, field
from typing import Optional
from config import EventStatus
from utils.id_generator import generate_event_id, timestamp


@dataclass
class Event:
    """Represents an event at Gran Tesoro or the Reverie Summit."""
    
    name: str
    description: str
    venue: str
    capacity: int
    event_date: str
    id: str = field(default_factory=generate_event_id)
    status: str = field(default=EventStatus.OPEN)
    created_at: str = field(default_factory=timestamp)
    updated_at: str = field(default_factory=timestamp)
    organizer: str = "Gild Tesoro's Golden Entertainment Division"
    category: str = "VIP Gala"
    
    def to_dict(self) -> dict:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "venue": self.venue,
            "capacity": self.capacity,
            "event_date": self.event_date,
            "status": self.status,
            "organizer": self.organizer,
            "category": self.category,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """Create Event from dictionary."""
        return cls(
            id=data.get("id", generate_event_id()),
            name=data["name"],
            description=data.get("description", ""),
            venue=data.get("venue", "Gran Tesoro"),
            capacity=data["capacity"],
            event_date=data["event_date"],
            status=data.get("status", EventStatus.OPEN),
            organizer=data.get("organizer", "Gild Tesoro's Golden Entertainment Division"),
            category=data.get("category", "VIP Gala"),
            created_at=data.get("created_at", timestamp()),
            updated_at=data.get("updated_at", timestamp()),
        )