"""
Event Service - Create, manage, and query events
"""
from typing import List, Optional, Dict

from models.event import Event
from config import EventStatus, RegistrationStatus
from storage.database import db
from utils.validators import (
    validate_required_string,
    validate_capacity,
    validate_positive_integer,
    ValidationError,
)
from utils.id_generator import timestamp
from utils.theme import FLAVOR_TEXT


class EventService:
    """Service for managing events at Gran Tesoro."""
    
    def create_event(
        self,
        name: str,
        description: str,
        venue: str,
        capacity: int,
        event_date: str,
        organizer: str = "Gild Tesoro's Golden Entertainment Division",
        category: str = "VIP Gala",
    ) -> Dict:
        """Create a new event."""
        # Validate inputs
        name = validate_required_string(name, "Event Name")
        description = validate_required_string(description, "Description")
        venue = validate_required_string(venue, "Venue")
        capacity = validate_capacity(capacity)
        event_date = validate_required_string(event_date, "Event Date")
        
        # Create event
        event = Event(
            name=name,
            description=description,
            venue=venue,
            capacity=capacity,
            event_date=event_date,
            organizer=organizer,
            category=category,
        )
        
        db.save_event(event)
        db.add_audit_entry("CREATE", "Event", event.id, f"Event '{name}' created with capacity {capacity}")
        
        return {
            "success": True,
            "message": FLAVOR_TEXT["event_created"],
            "event": event.to_dict(),
        }
    
    def get_event(self, event_id: str) -> Optional[Dict]:
        """Get event details with registration stats."""
        event = db.get_event(event_id)
        if not event:
            return None
        
        confirmed_count = db.get_active_registration_count(event_id)
        waitlist = db.get_event_waitlist(event_id)
        
        result = event.to_dict()
        result["stats"] = {
            "confirmed_registrations": confirmed_count,
            "available_seats": max(0, event.capacity - confirmed_count),
            "waitlist_count": len(waitlist),
            "is_full": confirmed_count >= event.capacity,
        }
        return result
    
    def list_events(self, status: str = None) -> List[Dict]:
        """List all events, optionally filtered by status."""
        events = db.get_all_events()
        if status:
            events = [e for e in events if e.status == status]
        
        results = []
        for event in events:
            confirmed = db.get_active_registration_count(event.id)
            waitlist = db.get_event_waitlist(event.id)
            data = event.to_dict()
            data["stats"] = {
                "confirmed_registrations": confirmed,
                "available_seats": max(0, event.capacity - confirmed),
                "waitlist_count": len(waitlist),
                "is_full": confirmed >= event.capacity,
            }
            results.append(data)
        return results
    
    def update_event(self, event_id: str, **kwargs) -> Dict:
        """Update event details."""
        event = db.get_event(event_id)
        if not event:
            return {"success": False, "message": "Event not found."}
        
        if "name" in kwargs:
            event.name = validate_required_string(kwargs["name"], "Event Name")
        if "description" in kwargs:
            event.description = kwargs["description"]
        if "venue" in kwargs:
            event.venue = validate_required_string(kwargs["venue"], "Venue")
        if "event_date" in kwargs:
            event.event_date = kwargs["event_date"]
        if "organizer" in kwargs:
            event.organizer = kwargs["organizer"]
        if "category" in kwargs:
            event.category = kwargs["category"]
        
        event.updated_at = timestamp()
        db.save_event(event)
        db.add_audit_entry("UPDATE", "Event", event.id, f"Event updated: {list(kwargs.keys())}")
        
        return {
            "success": True,
            "message": "Event updated successfully.",
            "event": event.to_dict(),
        }
    
    def update_capacity(self, event_id: str, new_capacity: int) -> Dict:
        """
        Update event capacity.
        If capacity increases, automatically promote waitlisted participants.
        """
        event = db.get_event(event_id)
        if not event:
            return {"success": False, "message": "Event not found."}
        
        current_confirmed = db.get_active_registration_count(event_id)
        new_capacity = validate_capacity(new_capacity, current_confirmed)
        
        old_capacity = event.capacity
        event.capacity = new_capacity
        event.updated_at = timestamp()
        
        # Update event status
        if current_confirmed < new_capacity:
            event.status = EventStatus.OPEN
        else:
            event.status = EventStatus.FULL
        
        db.save_event(event)
        db.add_audit_entry(
            "UPDATE_CAPACITY", "Event", event.id,
            f"Capacity changed from {old_capacity} to {new_capacity}"
        )
        
        result = {
            "success": True,
            "message": FLAVOR_TEXT["capacity_updated"],
            "event": event.to_dict(),
            "old_capacity": old_capacity,
            "new_capacity": new_capacity,
            "promotions_available": max(0, new_capacity - current_confirmed) if new_capacity > old_capacity else 0,
        }
        
        return result
    
    def close_event(self, event_id: str) -> Dict:
        """Close an event for new registrations."""
        event = db.get_event(event_id)
        if not event:
            return {"success": False, "message": "Event not found."}
        
        event.status = EventStatus.CLOSED
        event.updated_at = timestamp()
        db.save_event(event)
        db.add_audit_entry("CLOSE", "Event", event.id, "Event closed")
        
        return {
            "success": True,
            "message": FLAVOR_TEXT["event_closed"],
            "event": event.to_dict(),
        }
    
    def cancel_event(self, event_id: str) -> Dict:
        """Cancel an event entirely."""
        event = db.get_event(event_id)
        if not event:
            return {"success": False, "message": "Event not found."}
        
        event.status = EventStatus.CANCELLED
        event.updated_at = timestamp()
        db.save_event(event)
        
        # Cancel all registrations
        regs = db.get_event_registrations(event_id, status=RegistrationStatus.CONFIRMED)
        for reg in regs:
            reg.status = RegistrationStatus.CANCELLED
            reg.cancelled_at = timestamp()
            db.save_registration(reg)
        
        # Deactivate waitlist
        waitlist = db.get_event_waitlist(event_id)
        for entry in waitlist:
            entry.is_active = False
            db.save_waitlist_entry(entry)
        
        db.add_audit_entry(
            "CANCEL_EVENT", "Event", event.id,
            f"Event cancelled. {len(regs)} registrations and {len(waitlist)} waitlist entries affected."
        )
        
        return {
            "success": True,
            "message": "Event has been cancelled. All registrations and waitlist entries have been cancelled.",
            "cancelled_registrations": len(regs),
            "cancelled_waitlist": len(waitlist),
        }
    
    def get_event_summary(self, event_id: str) -> Optional[Dict]:
        """Get comprehensive event summary."""
        event = db.get_event(event_id)
        if not event:
            return None
        
        confirmed_regs = db.get_event_registrations(event_id, status=RegistrationStatus.CONFIRMED)
        cancelled_regs = db.get_event_registrations(event_id, status=RegistrationStatus.CANCELLED)
        waitlist = db.get_event_waitlist(event_id)
        pending_offers = db.get_pending_offers_for_event(event_id)
        
        # Get participant details for confirmed registrations
        confirmed_guests = []
        for reg in confirmed_regs:
            participant = db.get_participant(reg.participant_id)
            if participant:
                confirmed_guests.append({
                    "registration": reg.to_dict(),
                    "participant": participant.to_dict(),
                })
        
        # Get participant details for waitlist
        waitlist_guests = []
        for entry in waitlist:
            participant = db.get_participant(entry.participant_id)
            if participant:
                waitlist_guests.append({
                    "waitlist_entry": entry.to_dict(),
                    "participant": participant.to_dict(),
                })
        
        return {
            "event": event.to_dict(),
            "stats": {
                "capacity": event.capacity,
                "confirmed_count": len(confirmed_regs),
                "cancelled_count": len(cancelled_regs),
                "waitlist_count": len(waitlist),
                "pending_offers": len(pending_offers),
                "available_seats": max(0, event.capacity - len(confirmed_regs)),
                "occupancy_percentage": round(
                    (len(confirmed_regs) / event.capacity * 100) if event.capacity > 0 else 0, 1
                ),
            },
            "confirmed_guests": confirmed_guests,
            "waitlist_guests": waitlist_guests,
            "pending_offers": [o.to_dict() for o in pending_offers],
        }