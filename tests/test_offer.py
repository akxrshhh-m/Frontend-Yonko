"""
Tests for Offer Service
"""
import pytest
from datetime import datetime, timedelta
from services.event_service import EventService
from services.registration_service import RegistrationService
from services.offer_service import OfferService
from services.waitlist_service import WaitlistService
from models.offer import SeatOffer
from storage.database import Database
from config import OfferStatus


@pytest.fixture(autouse=True)
def reset_db():
    db = Database()
    db.reset()
    yield
    db.reset()


@pytest.fixture
def event_with_waitlist():
    """Create a full event with a waitlisted participant."""
    event_service = EventService()
    reg_service = RegistrationService()
    
    result = event_service.create_event(
        name="Offer Test Event", description="Test", venue="Test",
        capacity=2, event_date="2025-12-31",
    )
    event_id = result["event"]["id"]
    
    reg_service.register_participant(event_id, "Guest A", "a@test.com")
    reg_service.register_participant(event_id, "Guest B", "b@test.com")
    reg_service.register_participant(event_id, "Waiter 1", "w1@test.com")
    reg_service.register_participant(event_id, "Waiter 2", "w2@test.com")
    
    return event_id


class TestOfferCreation:
    def test_offer_created_on_cancellation(self, event_with_waitlist):
        reg_service = RegistrationService()
        
        result = reg_service.cancel_registration(
            event_with_waitlist, email="a@test.com"
        )
        
        assert result["success"] is True
        assert "waitlist_offer" in result
        assert result["waitlist_offer"]["success"] is True
        assert "offer" in result["waitlist_offer"]
    
    def test_offer_has_expiration(self, event_with_waitlist):
        reg_service = RegistrationService()
        
        result = reg_service.cancel_registration(
            event_with_waitlist, email="a@test.com"
        )
        
        offer_data = result["waitlist_offer"]["offer"]
        assert offer_data["expires_at"] != ""
        assert offer_data["time_remaining_seconds"] > 0
    
    def test_no_offer_when_waitlist_empty(self):
        event_service = EventService()
        reg_service = RegistrationService()
        
        result = event_service.create_event(
            name="No Waitlist", description="Test", venue="Test",
            capacity=5, event_date="2025-12-31",
        )
        event_id = result["event"]["id"]
        
        reg_service.register_participant(event_id, "Guest A", "a@test.com")
        
        cancel_result = reg_service.cancel_registration(event_id, email="a@test.com")
        assert cancel_result["success"] is True
        assert cancel_result.get("waitlist_status") is not None


class TestAcceptOffer:
    def test_accept_valid_offer(self, event_with_waitlist):
        reg_service = RegistrationService()
        offer_service = OfferService()
        
        cancel_result = reg_service.cancel_registration(
            event_with_waitlist, email="a@test.com"
        )
        
        offer_id = cancel_result["waitlist_offer"]["offer"]["id"]
        
        accept_result = offer_service.accept_offer(offer_id)
        assert accept_result["success"] is True
        assert accept_result["offer"]["status"] == OfferStatus.ACCEPTED
    
    def test_accept_creates_registration(self, event_with_waitlist):
        reg_service = RegistrationService()
        offer_service = OfferService()
        db = Database()
        
        cancel_result = reg_service.cancel_registration(
            event_with_waitlist, email="a@test.com"
        )
        
        offer_id = cancel_result["waitlist_offer"]["offer"]["id"]
        participant_id = cancel_result["waitlist_offer"]["offer"]["participant_id"]
        
        offer_service.accept_offer(offer_id)
        
        # Verify registration was created
        reg = db.find_registration(event_with_waitlist, participant_id)
        assert reg is not None
        assert reg.status == "CONFIRMED"


class TestDeclineOffer:
    def test_decline_offer(self, event_with_waitlist):
        reg_service = RegistrationService()
        offer_service = OfferService()
        
        cancel_result = reg_service.cancel_registration(
            event_with_waitlist, email="a@test.com"
        )
        
        offer_id = cancel_result["waitlist_offer"]["offer"]["id"]
        
        decline_result = offer_service.decline_offer(offer_id)
        assert decline_result["success"] is True
        assert decline_result["declined_offer"]["status"] == OfferStatus.DECLINED
    
    def test_decline_offers_to_next(self, event_with_waitlist):
        reg_service = RegistrationService()
        offer_service = OfferService()
        
        cancel_result = reg_service.cancel_registration(
            event_with_waitlist, email="a@test.com"
        )
        
        offer_id = cancel_result["waitlist_offer"]["offer"]["id"]
        
        decline_result = offer_service.decline_offer(offer_id)
        
        # Should have created a new offer for the next person
        assert decline_result.get("next_offer") is not None


class TestOfferExpiration:
    def test_expired_offer_detection(self):
        """Test that offers correctly detect expiration."""
        offer = SeatOffer(
            event_id="test",
            participant_id="test",
            waitlist_entry_id="test",
            expiration_seconds=0,  # Expires immediately
        )
        # Force past expiry
        past = (datetime.utcnow() - timedelta(seconds=10)).isoformat() + "Z"
        offer.expires_at = past
        
        assert offer.is_expired is True
        assert offer.time_remaining_seconds == 0
    
    def test_valid_offer_not_expired(self):
        """Test that valid offers are not expired."""
        offer = SeatOffer(
            event_id="test",
            participant_id="test",
            waitlist_entry_id="test",
            expiration_seconds=300,
        )
        
        assert offer.is_expired is False
        assert offer.time_remaining_seconds > 0