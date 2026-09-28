"""
Waitlist Service - Silver Room Queue Management
Manages fair FIFO waitlist for events at capacity.
"""
from typing import Dict, List, Optional

from models.waitlist_entry import WaitlistEntry
from storage.database import db
from config import RegistrationStatus
from utils.id_generator import timestamp
from utils.theme import FLAVOR_TEXT, get_rank_title


class WaitlistService:
    """Service for managing the waitlist (Silver Room Queue)."""
    
    def add_to_waitlist(self, event_id: str, participant_id: str) -> Dict:
        """Add a participant to the event waitlist."""
        event = db.get_event(event_id)
        if not event:
            return {"success": False, "message": "Event not found.", "code": "EVENT_NOT_FOUND"}
        
        participant = db.get_participant(participant_id)
        if not participant:
            return {"success": False, "message": "Participant not found.", "code": "PARTICIPANT_NOT_FOUND"}
        
        # Check if already on waitlist
        existing = db.find_waitlist_entry(event_id, participant_id)
        if existing:
            return {
                "success": False,
                "message": "Participant is already on the waitlist.",
                "code": "ALREADY_WAITLISTED",
                "waitlist_entry": existing.to_dict(),
            }
        
        # Check if already registered
        existing_reg = db.find_registration(event_id, participant_id)
        if existing_reg and existing_reg.status == RegistrationStatus.CONFIRMED:
            return {
                "success": False,
                "message": "Participant is already registered.",
                "code": "ALREADY_REGISTERED",
            }
        
        # Determine position
        position = db.get_next_waitlist_position(event_id)
        rank_title = get_rank_title(position)
        
        entry = WaitlistEntry(
            event_id=event_id,
            participant_id=participant_id,
            position=position,
            rank_title=rank_title,
        )
        
        db.save_waitlist_entry(entry)
        db.add_audit_entry(
            "ADD_WAITLIST", "WaitlistEntry", entry.id,
            f"Participant {participant.name} added to waitlist at position #{position} for {event.name}"
        )
        
        return {
            "success": True,
            "message": FLAVOR_TEXT["registration_waitlisted"],
            "type": "WAITLISTED",
            "waitlist_entry": entry.to_dict(),
            "participant": participant.to_dict(),
            "position": position,
            "rank_title": rank_title,
        }
    
    def get_waitlist(self, event_id: str) -> Dict:
        """Get the full waitlist for an event."""
        event = db.get_event(event_id)
        if not event:
            return {"success": False, "message": "Event not found."}
        
        entries = db.get_event_waitlist(event_id, active_only=True)
        
        waitlist_with_participants = []
        for entry in entries:
            participant = db.get_participant(entry.participant_id)
            waitlist_with_participants.append({
                "waitlist_entry": entry.to_dict(),
                "participant": participant.to_dict() if participant else None,
            })
        
        return {
            "success": True,
            "event": event.to_dict(),
            "waitlist_count": len(entries),
            "waitlist": waitlist_with_participants,
        }
    
    def get_next_in_line(self, event_id: str) -> Optional[WaitlistEntry]:
        """Get the next person in line on the waitlist."""
        entries = db.get_event_waitlist(event_id, active_only=True)
        return entries[0] if entries else None
    
    def remove_from_waitlist(self, event_id: str, participant_id: str) -> Dict:
        """Remove a participant from the waitlist."""
        entry = db.find_waitlist_entry(event_id, participant_id)
        if not entry:
            return {"success": False, "message": "Waitlist entry not found.", "code": "NOT_FOUND"}
        
        entry.is_active = False
        db.save_waitlist_entry(entry)
        
        participant = db.get_participant(participant_id)
        db.add_audit_entry(
            "REMOVE_WAITLIST", "WaitlistEntry", entry.id,
            f"Participant {participant.name if participant else 'Unknown'} removed from waitlist"
        )
        
        # Re-number remaining active entries
        self._renumber_waitlist(event_id)
        
        return {
            "success": True,
            "message": "Removed from waitlist.",
            "removed_entry": entry.to_dict(),
        }
    
    def _renumber_waitlist(self, event_id: str):
        """Re-number waitlist positions after a removal to maintain consistency."""
        entries = db.get_event_waitlist(event_id, active_only=True)
        for idx, entry in enumerate(entries, start=1):
            if entry.position != idx:
                entry.position = idx
                entry.rank_title = get_rank_title(idx)
                db.save_waitlist_entry(entry)
    
    def promote_from_waitlist(self, event_id: str, waitlist_entry_id: str) -> Dict:
        """
        Promote a waitlisted participant to confirmed registration.
        Used when an offer is accepted or for direct promotion.
        """
        from services.registration_service import RegistrationService
        
        entry = db.get_waitlist_entry(waitlist_entry_id)
        if not entry or not entry.is_active:
            return {"success": False, "message": "Waitlist entry not found or inactive."}
        
        event = db.get_event(event_id)
        if not event:
            return {"success": False, "message": "Event not found."}
        
        participant = db.get_participant(entry.participant_id)
        if not participant:
            return {"success": False, "message": "Participant not found."}
        
        # Check if there's actually a seat available
        confirmed_count = db.get_active_registration_count(event_id)
        if confirmed_count >= event.capacity:
            return {"success": False, "message": "No available seats.", "code": "NO_SEATS"}
        
        # Deactivate waitlist entry
        entry.is_active = False
        db.save_waitlist_entry(entry)
        
        # Create confirmed registration
        from models.registration import Registration
        from utils.theme import get_vip_tier
        
        reg_number = confirmed_count + 1
        registration = Registration(
            event_id=event_id,
            participant_id=entry.participant_id,
            status=RegistrationStatus.CONFIRMED,
            registration_number=reg_number,
            vip_tier=get_vip_tier(reg_number, event.capacity),
        )
        db.save_registration(registration)
        
        # Update event status
        new_count = db.get_active_registration_count(event_id)
        if new_count >= event.capacity:
            event.status = "FULL"
            event.updated_at = timestamp()
            db.save_event(event)
        
        # Renumber waitlist
        self._renumber_waitlist(event_id)
        
        db.add_audit_entry(
            "PROMOTE_WAITLIST", "Registration", registration.id,
            f"Participant {participant.name} promoted from waitlist to confirmed (#{reg_number})"
        )
        
        return {
            "success": True,
            "message": FLAVOR_TEXT["offer_accepted"],
            "registration": registration.to_dict(),
            "participant": participant.to_dict(),
        }