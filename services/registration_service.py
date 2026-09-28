"""
Registration Service - Handle participant registration for events
"""
from typing import Dict, Optional

from models.participant import Participant
from models.registration import Registration
from config import RegistrationStatus, EventStatus
from storage.database import db
from utils.validators import validate_required_string, validate_email, ValidationError
from utils.id_generator import timestamp
from utils.theme import FLAVOR_TEXT, get_vip_tier


class RegistrationService:
    """Service for managing event registrations."""
    
    def register_participant(
        self,
        event_id: str,
        name: str,
        email: str,
        phone: str = "",
        affiliation: str = "Independent",
        auto_waitlist: bool = True,
    ) -> Dict:
        """
        Register a participant for an event.
        If event is full and auto_waitlist is True, add to waitlist.
        
        Returns result dict with registration or waitlist info.
        """
        # Validate inputs
        name = validate_required_string(name, "Name")
        email = validate_email(email)
        
        # Validate event exists and is open
        event = db.get_event(event_id)
        if not event:
            return {"success": False, "message": "Event not found.", "code": "EVENT_NOT_FOUND"}
        
        if event.status in (EventStatus.CLOSED, EventStatus.CANCELLED):
            return {
                "success": False,
                "message": FLAVOR_TEXT["event_closed"],
                "code": "EVENT_CLOSED",
            }
        
        # Find or create participant
        participant = db.get_participant_by_email(email)
        if not participant:
            participant = Participant(
                name=name,
                email=email,
                phone=phone,
                affiliation=affiliation,
            )
            db.save_participant(participant)
            db.add_audit_entry("CREATE", "Participant", participant.id, f"New participant: {name}")
        
        # Check if already registered
        existing_reg = db.find_registration(event_id, participant.id)
        if existing_reg and existing_reg.status == RegistrationStatus.CONFIRMED:
            return {
                "success": False,
                "message": "Participant is already registered for this event.",
                "code": "ALREADY_REGISTERED",
                "registration": existing_reg.to_dict(),
            }
        
        # Check if already on waitlist
        existing_wl = db.find_waitlist_entry(event_id, participant.id)
        if existing_wl:
            return {
                "success": False,
                "message": "Participant is already on the waitlist for this event.",
                "code": "ALREADY_WAITLISTED",
                "waitlist_entry": existing_wl.to_dict(),
            }
        
        # Check capacity
        confirmed_count = db.get_active_registration_count(event_id)
        
        if confirmed_count < event.capacity:
            # Seat available - confirm registration
            reg_number = confirmed_count + 1
            vip_tier = get_vip_tier(reg_number, event.capacity)
            
            registration = Registration(
                event_id=event_id,
                participant_id=participant.id,
                status=RegistrationStatus.CONFIRMED,
                registration_number=reg_number,
                vip_tier=vip_tier,
            )
            db.save_registration(registration)
            
            # Check if event is now full
            new_count = db.get_active_registration_count(event_id)
            if new_count >= event.capacity:
                event.status = EventStatus.FULL
                event.updated_at = timestamp()
                db.save_event(event)
            
            db.add_audit_entry(
                "REGISTER", "Registration", registration.id,
                f"Participant {name} registered for event {event.name} (Seat #{reg_number})"
            )
            
            return {
                "success": True,
                "message": FLAVOR_TEXT["registration_success"],
                "type": "CONFIRMED",
                "registration": registration.to_dict(),
                "participant": participant.to_dict(),
                "vip_tier": vip_tier,
            }
        else:
            # Event is full
            if not auto_waitlist:
                return {
                    "success": False,
                    "message": FLAVOR_TEXT["event_full"],
                    "code": "EVENT_FULL",
                }
            
            # Add to waitlist
            from services.waitlist_service import WaitlistService
            waitlist_service = WaitlistService()
            return waitlist_service.add_to_waitlist(event_id, participant.id)
    
    def cancel_registration(self, event_id: str, participant_id: str = None, 
                           email: str = None, registration_id: str = None) -> Dict:
        """
        Cancel a registration. 
        Triggers waitlist promotion if there are waitlisted participants.
        """
        # Find the registration
        registration = None
        
        if registration_id:
            registration = db.get_registration(registration_id)
        elif participant_id:
            registration = db.find_registration(event_id, participant_id)
        elif email:
            participant = db.get_participant_by_email(email)
            if participant:
                registration = db.find_registration(event_id, participant.id)
        
        if not registration:
            return {"success": False, "message": "Registration not found.", "code": "REG_NOT_FOUND"}
        
        if registration.status == RegistrationStatus.CANCELLED:
            return {
                "success": False,
                "message": "Registration is already cancelled.",
                "code": "ALREADY_CANCELLED",
            }
        
        event = db.get_event(registration.event_id)
        if not event:
            return {"success": False, "message": "Event not found.", "code": "EVENT_NOT_FOUND"}
        
        # Cancel the registration
        registration.status = RegistrationStatus.CANCELLED
        registration.cancelled_at = timestamp()
        db.save_registration(registration)
        
        # Update event status
        if event.status == EventStatus.FULL:
            event.status = EventStatus.OPEN
            event.updated_at = timestamp()
            db.save_event(event)
        
        participant = db.get_participant(registration.participant_id)
        participant_name = participant.name if participant else "Unknown"
        
        db.add_audit_entry(
            "CANCEL_REGISTRATION", "Registration", registration.id,
            f"Participant {participant_name} cancelled registration for {event.name}"
        )
        
        # Trigger waitlist promotion
        from services.offer_service import OfferService
        offer_service = OfferService()
        offer_result = offer_service.offer_seat_to_next_in_waitlist(event.id)
        
        result = {
            "success": True,
            "message": FLAVOR_TEXT["cancellation"],
            "cancelled_registration": registration.to_dict(),
            "participant_name": participant_name,
        }
        
        if offer_result.get("success"):
            result["waitlist_offer"] = offer_result
        else:
            result["waitlist_status"] = offer_result.get("message", "No one on waitlist")
        
        return result
    
    def get_participant_registrations(self, participant_id: str = None, 
                                      email: str = None) -> Dict:
        """Get all registrations for a participant."""
        participant = None
        if participant_id:
            participant = db.get_participant(participant_id)
        elif email:
            participant = db.get_participant_by_email(email)
        
        if not participant:
            return {"success": False, "message": "Participant not found."}
        
        # Find all registrations
        all_regs = []
        for reg in db.registrations.values():
            if reg.participant_id == participant.id:
                event = db.get_event(reg.event_id)
                all_regs.append({
                    "registration": reg.to_dict(),
                    "event": event.to_dict() if event else None,
                })
        
        # Find all waitlist entries
        all_waitlist = []
        for entry in db.waitlist_entries.values():
            if entry.participant_id == participant.id and entry.is_active:
                event = db.get_event(entry.event_id)
                all_waitlist.append({
                    "waitlist_entry": entry.to_dict(),
                    "event": event.to_dict() if event else None,
                })
        
        # Find all pending offers
        all_offers = []
        for offer in db.offers.values():
            if offer.participant_id == participant.id:
                event = db.get_event(offer.event_id)
                all_offers.append({
                    "offer": offer.to_dict(),
                    "event": event.to_dict() if event else None,
                })
        
        return {
            "success": True,
            "participant": participant.to_dict(),
            "registrations": all_regs,
            "waitlist_entries": all_waitlist,
            "pending_offers": all_offers,
        }