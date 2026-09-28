"""
Notification Service - Golden Den Den Mushi Communications
Handles sending notifications for various events.
(In production, this would integrate with email/SMS/push notification services)
"""
from typing import Optional
from models.offer import SeatOffer
from models.participant import Participant
from models.event import Event
from utils.theme import FLAVOR_TEXT
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Notification service - simulates sending notifications.
    In production, this would integrate with SendGrid, Twilio, Firebase, etc.
    """
    
    def __init__(self):
        self.sent_notifications = []
    
    def send_offer_notification(self, offer: SeatOffer, participant: Optional[Participant], 
                                 event: Optional[Event]):
        """Send notification about a seat offer (Golden Den Den Mushi call)."""
        notification = {
            "type": "SEAT_OFFER",
            "recipient": participant.email if participant else "unknown",
            "recipient_name": participant.name if participant else "Unknown",
            "subject": f"🎰 Golden Den Den Mushi Call - Seat Available at {event.name if event else 'Event'}!",
            "body": (
                f"Congratulations, {participant.name if participant else 'Guest'}!\n\n"
                f"A seat has become available at '{event.name if event else 'the event'}'.\n"
                f"Venue: {event.venue if event else 'TBD'}\n"
                f"Date: {event.event_date if event else 'TBD'}\n\n"
                f"You have {offer.time_remaining_seconds} seconds to accept this offer.\n"
                f"Offer ID: {offer.id}\n\n"
                f"To accept: Use offer ID '{offer.id}' to confirm your seat.\n"
                f"If you don't respond in time, the offer will go to the next person.\n\n"
                f"— Gild Tesoro's Golden Entertainment Division"
            ),
            "offer_id": offer.id,
            "expires_at": offer.expires_at,
        }
        
        self.sent_notifications.append(notification)
        logger.info(
            f"📞 [NOTIFICATION] Seat offer sent to {participant.name if participant else 'Unknown'} "
            f"({participant.email if participant else 'N/A'}) for event '{event.name if event else 'N/A'}'"
        )
        
        # In production: send_email(notification), send_sms(notification), etc.
        print(f"\n📞 [Golden Den Den Mushi] Calling {participant.name if participant else 'Guest'}...")
        print(f"   📧 Notification sent to: {participant.email if participant else 'N/A'}")
        print(f"   ⏰ Offer expires at: {offer.expires_at}")
        print(f"   🎫 Offer ID: {offer.id}\n")
    
    def send_acceptance_confirmation(self, offer: SeatOffer, participant: Optional[Participant],
                                       event: Optional[Event]):
        """Send confirmation after offer acceptance."""
        notification = {
            "type": "OFFER_ACCEPTED",
            "recipient": participant.email if participant else "unknown",
            "subject": f"🌟 Welcome to the VIP Gold Room - {event.name if event else 'Event'}!",
            "body": (
                f"Welcome, {participant.name if participant else 'Guest'}!\n\n"
                f"Your seat at '{event.name if event else 'the event'}' is confirmed!\n"
                f"You are now a VIP Gold Room guest.\n\n"
                f"— Gild Tesoro's Golden Entertainment Division"
            ),
        }
        self.sent_notifications.append(notification)
        logger.info(f"✅ [NOTIFICATION] Acceptance confirmation sent to {participant.name if participant else 'Unknown'}")
        print(f"\n🌟 [Confirmation] {participant.name if participant else 'Guest'} is now a VIP Gold Room guest!")
    
    def send_expiration_notification(self, offer: SeatOffer, participant: Optional[Participant],
                                       event: Optional[Event]):
        """Send notification that an offer has expired."""
        notification = {
            "type": "OFFER_EXPIRED",
            "recipient": participant.email if participant else "unknown",
            "subject": f"⏰ Seat Offer Expired - {event.name if event else 'Event'}",
            "body": (
                f"Dear {participant.name if participant else 'Guest'},\n\n"
                f"Your seat offer for '{event.name if event else 'the event'}' has expired.\n"
                f"The seat will be offered to the next person in line.\n\n"
                f"— Gild Tesoro's Golden Entertainment Division"
            ),
        }
        self.sent_notifications.append(notification)
        logger.info(f"⏰ [NOTIFICATION] Expiration notice sent to {participant.name if participant else 'Unknown'}")
    
    def send_registration_confirmation(self, participant: Participant, event: Event, 
                                         vip_tier: str):
        """Send registration confirmation."""
        notification = {
            "type": "REGISTRATION_CONFIRMED",
            "recipient": participant.email,
            "subject": f"🎉 Registration Confirmed - {event.name}",
            "body": (
                f"Welcome, {participant.name}!\n\n"
                f"Your registration for '{event.name}' is confirmed!\n"
                f"VIP Tier: {vip_tier}\n"
                f"Venue: {event.venue}\n"
                f"Date: {event.event_date}\n\n"
                f"— Gild Tesoro's Golden Entertainment Division"
            ),
        }
        self.sent_notifications.append(notification)
        logger.info(f"🎉 [NOTIFICATION] Registration confirmation sent to {participant.name}")
    
    def send_waitlist_confirmation(self, participant: Participant, event: Event, 
                                     position: int, rank_title: str):
        """Send waitlist confirmation."""
        notification = {
            "type": "WAITLISTED",
            "recipient": participant.email,
            "subject": f"📋 Waitlisted - {event.name}",
            "body": (
                f"Dear {participant.name},\n\n"
                f"'{event.name}' is currently at full capacity.\n"
                f"You have been placed on the Silver Room Queue.\n"
                f"Position: #{position} ({rank_title})\n\n"
                f"We will notify you immediately if a seat becomes available.\n\n"
                f"— Gild Tesoro's Golden Entertainment Division"
            ),
        }
        self.sent_notifications.append(notification)
        logger.info(f"📋 [NOTIFICATION] Waitlist confirmation sent to {participant.name} (Position #{position})")