"""
Offer Service - Golden Den Den Mushi Invitation Management
Handles timed seat offers to waitlisted participants.
"""
from typing import Dict, Optional
from datetime import datetime

from models.offer import SeatOffer
from config import OfferStatus, OFFER_EXPIRATION_SECONDS
from storage.database import db
from utils.id_generator import timestamp
from utils.theme import FLAVOR_TEXT


class OfferService:
    """Service for managing timed seat offers."""
    
    def offer_seat_to_next_in_waitlist(self, event_id: str) -> Dict:
        """
        Create a timed offer for the next person in the waitlist.
        This is triggered when a cancellation frees up a seat.
        """
        from services.waitlist_service import WaitlistService
        waitlist_service = WaitlistService()
        
        event = db.get_event(event_id)
        if not event:
            return {"success": False, "message": "Event not found."}
        
        # Check if there are any pending offers already
        pending = db.get_pending_offers_for_event(event_id)
        # Check for expired offers and process them
        for offer in pending:
            if offer.is_expired:
                self._expire_offer(offer)
        
        # Re-check pending offers after expiration processing
        pending = db.get_pending_offers_for_event(event_id)
        if pending:
            return {
                "success": False,
                "message": "There is already a pending offer for this event. Waiting for response.",
                "pending_offer": pending[0].to_dict(),
            }
        
        # Check if there's actually a seat available
        confirmed_count = db.get_active_registration_count(event_id)
        if confirmed_count >= event.capacity:
            return {"success": False, "message": "No seats available."}
        
        # Get next in line
        next_entry = waitlist_service.get_next_in_line(event_id)
        if not next_entry:
            return {
                "success": False,
                "message": FLAVOR_TEXT["waitlist_empty"],
                "code": "WAITLIST_EMPTY",
            }
        
        # Create the offer
        offer = SeatOffer(
            event_id=event_id,
            participant_id=next_entry.participant_id,
            waitlist_entry_id=next_entry.id,
        )
        db.save_offer(offer)
        
        participant = db.get_participant(next_entry.participant_id)
        
        db.add_audit_entry(
            "CREATE_OFFER", "SeatOffer", offer.id,
            f"Seat offer created for {participant.name if participant else 'Unknown'} "
            f"(waitlist position #{next_entry.position}). Expires in {OFFER_EXPIRATION_SECONDS}s"
        )
        
        # Trigger notification
        from services.notification_service import NotificationService
        notifier = NotificationService()
        notifier.send_offer_notification(offer, participant, event)
        
        return {
            "success": True,
            "message": FLAVOR_TEXT["offer_sent"],
            "offer": offer.to_dict(),
            "participant": participant.to_dict() if participant else None,
            "expires_in_seconds": offer.time_remaining_seconds,
        }
    
    def accept_offer(self, offer_id: str) -> Dict:
        """Accept a seat offer and promote to confirmed registration."""
        offer = db.get_offer(offer_id)
        if not offer:
            return {"success": False, "message": "Offer not found.", "code": "OFFER_NOT_FOUND"}
        
        # Check if expired
        if offer.is_expired:
            self._expire_offer(offer)
            return {
                "success": False,
                "message": FLAVOR_TEXT["offer_expired"],
                "code": "OFFER_EXPIRED",
            }
        
        if offer.status != OfferStatus.PENDING:
            return {
                "success": False,
                "message": f"Offer is no longer pending (status: {offer.status}).",
                "code": "OFFER_NOT_PENDING",
            }
        
        # Accept the offer
        offer.status = OfferStatus.ACCEPTED
        offer.responded_at = timestamp()
        db.save_offer(offer)
        
        # Promote from waitlist to confirmed
        from services.waitlist_service import WaitlistService
        waitlist_service = WaitlistService()
        promotion_result = waitlist_service.promote_from_waitlist(
            offer.event_id, offer.waitlist_entry_id
        )
        
        if promotion_result.get("success"):
            participant = db.get_participant(offer.participant_id)
            
            db.add_audit_entry(
                "ACCEPT_OFFER", "SeatOffer", offer.id,
                f"Offer accepted by {participant.name if participant else 'Unknown'}"
            )
            
            # Notify
            from services.notification_service import NotificationService
            notifier = NotificationService()
            notifier.send_acceptance_confirmation(offer, participant, db.get_event(offer.event_id))
            
            return {
                "success": True,
                "message": FLAVOR_TEXT["offer_accepted"],
                "offer": offer.to_dict(),
                "registration": promotion_result.get("registration"),
            }
        else:
            # Rollback offer status if promotion fails
            offer.status = OfferStatus.PENDING
            offer.responded_at = None
            db.save_offer(offer)
            return {
                "success": False,
                "message": f"Failed to promote: {promotion_result.get('message')}",
            }
    
    def decline_offer(self, offer_id: str) -> Dict:
        """Decline a seat offer. The offer goes to the next person in line."""
        offer = db.get_offer(offer_id)
        if not offer:
            return {"success": False, "message": "Offer not found.", "code": "OFFER_NOT_FOUND"}
        
        if offer.status != OfferStatus.PENDING:
            return {
                "success": False,
                "message": f"Offer is no longer pending (status: {offer.status}).",
                "code": "OFFER_NOT_PENDING",
            }
        
        # Decline the offer
        offer.status = OfferStatus.DECLINED
        offer.responded_at = timestamp()
        db.save_offer(offer)
        
        # Remove from waitlist
        from services.waitlist_service import WaitlistService
        waitlist_service = WaitlistService()
        
        entry = db.get_waitlist_entry(offer.waitlist_entry_id)
        if entry:
            entry.is_active = False
            db.save_waitlist_entry(entry)
            waitlist_service._renumber_waitlist(offer.event_id)
        
        participant = db.get_participant(offer.participant_id)
        
        db.add_audit_entry(
            "DECLINE_OFFER", "SeatOffer", offer.id,
            f"Offer declined by {participant.name if participant else 'Unknown'}"
        )
        
        # Offer to next person
        next_offer_result = self.offer_seat_to_next_in_waitlist(offer.event_id)
        
        return {
            "success": True,
            "message": FLAVOR_TEXT["offer_declined"],
            "declined_offer": offer.to_dict(),
            "next_offer": next_offer_result if next_offer_result.get("success") else None,
        }
    
    def check_and_expire_offers(self, event_id: str = None) -> Dict:
        """Check all pending offers and expire any that have timed out."""
        expired_count = 0
        next_offers = []
        
        if event_id:
            pending = db.get_pending_offers_for_event(event_id)
        else:
            pending = [o for o in db.offers.values() if o.status == OfferStatus.PENDING]
        
        for offer in pending:
            if offer.is_expired:
                self._expire_offer(offer)
                expired_count += 1
                
                # Offer to next person
                next_result = self.offer_seat_to_next_in_waitlist(offer.event_id)
                if next_result.get("success"):
                    next_offers.append(next_result)
        
        return {
            "success": True,
            "expired_count": expired_count,
            "next_offers_created": len(next_offers),
            "next_offers": next_offers,
        }
    
    def get_offer_status(self, offer_id: str) -> Dict:
        """Get the current status of an offer."""
        offer = db.get_offer(offer_id)
        if not offer:
            return {"success": False, "message": "Offer not found."}
        
        # Check for expiration
        if offer.status == OfferStatus.PENDING and offer.is_expired:
            self._expire_offer(offer)
        
        participant = db.get_participant(offer.participant_id)
        event = db.get_event(offer.event_id)
        
        return {
            "success": True,
            "offer": offer.to_dict(),
            "participant": participant.to_dict() if participant else None,
            "event": event.to_dict() if event else None,
        }
    
    def _expire_offer(self, offer: SeatOffer):
        """Mark an offer as expired and handle cleanup."""
        offer.status = OfferStatus.EXPIRED
        offer.responded_at = timestamp()
        db.save_offer(offer)
        
        # Remove participant from waitlist (they didn't respond)
        entry = db.get_waitlist_entry(offer.waitlist_entry_id)
        if entry:
            entry.is_active = False
            db.save_waitlist_entry(entry)
            
            from services.waitlist_service import WaitlistService
            WaitlistService()._renumber_waitlist(offer.event_id)
        
        participant = db.get_participant(offer.participant_id)
        
        db.add_audit_entry(
            "EXPIRE_OFFER", "SeatOffer", offer.id,
            f"Offer expired for {participant.name if participant else 'Unknown'} (no response)"
        )
        
        # Notify
        from services.notification_service import NotificationService
        notifier = NotificationService()
        notifier.send_expiration_notification(offer, participant, db.get_event(offer.event_id))