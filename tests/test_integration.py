"""
Integration Tests - Full workflow scenarios
"""
import pytest
from services.event_service import EventService
from services.registration_service import RegistrationService
from services.waitlist_service import WaitlistService
from services.offer_service import OfferService
from storage.database import Database
from config import RegistrationStatus, EventStatus, OfferStatus


@pytest.fixture(autouse=True)
def reset_db():
    db = Database()
    db.reset()
    yield
    db.reset()


class TestFullRegistrationWorkflow:
    """Test complete registration → waitlist → cancellation → offer → acceptance flow."""
    
    def test_complete_workflow(self):
        event_service = EventService()
        reg_service = RegistrationService()
        offer_service = OfferService()
        db = Database()
        
        # 1. Create event with capacity 2
        event_result = event_service.create_event(
            name="Reverie Summit", description="World Government meeting",
            venue="Marijoa", capacity=2, event_date="2025-06-15",
        )
        event_id = event_result["event"]["id"]
        assert event_result["success"] is True
        
        # 2. Register 2 participants (fills capacity)
        reg1 = reg_service.register_participant(event_id, "Cobra", "cobra@alabasta.com")
        assert reg1["type"] == "CONFIRMED"
        
        reg2 = reg_service.register_participant(event_id, "Riku", "riku@dressrosa.com")
        assert reg2["type"] == "CONFIRMED"
        
        # 3. Verify event is full
        event_data = event_service.get_event(event_id)
        assert event_data["stats"]["is_full"] is True
        assert event_data["stats"]["available_seats"] == 0
        
        # 4. Attempt registration - should be waitlisted
        reg3 = reg_service.register_participant(event_id, "Dalton", "dalton@drum.com")
        assert reg3["type"] == "WAITLISTED"
        assert reg3["waitlist_entry"]["position"] == 1
        
        reg4 = reg_service.register_participant(event_id, "Neptune", "neptune@fishman.com")
        assert reg4["type"] == "WAITLISTED"
        assert reg4["waitlist_entry"]["position"] == 2
        
        # 5. Cancel first registration
        cancel_result = reg_service.cancel_registration(event_id, email="cobra@alabasta.com")
        assert cancel_result["success"] is True
        
        # 6. Verify offer was created for first waitlisted person (Dalton)
        assert "waitlist_offer" in cancel_result
        assert cancel_result["waitlist_offer"]["success"] is True
        offer_id = cancel_result["waitlist_offer"]["offer"]["id"]
        
        # 7. Accept the offer
        accept_result = offer_service.accept_offer(offer_id)
        assert accept_result["success"] is True
        
        # 8. Verify Dalton is now confirmed
        dalton_participant = db.get_participant_by_email("dalton@drum.com")
        dalton_reg = db.find_registration(event_id, dalton_participant.id)
        assert dalton_reg is not None
        assert dalton_reg.status == RegistrationStatus.CONFIRMED
        
        # 9. Verify Neptune is still on waitlist (position 1 now)
        waitlist_service = WaitlistService()
        waitlist = waitlist_service.get_waitlist(event_id)
        assert waitlist["waitlist_count"] == 1
        assert waitlist["waitlist"][0]["participant"]["email"] == "neptune@fishman.com"
        assert waitlist["waitlist"][0]["waitlist_entry"]["position"] == 1
        
        # 10. Verify event summary
        summary = event_service.get_event_summary(event_id)
        assert summary["stats"]["confirmed_count"] == 2
        assert summary["stats"]["cancelled_count"] == 1
        assert summary["stats"]["waitlist_count"] == 1
    
    def test_decline_cascades_to_next(self):
        """Test that declining an offer cascades to the next person."""
        event_service = EventService()
        reg_service = RegistrationService()
        offer_service = OfferService()
        
        # Create event with capacity 1
        event_result = event_service.create_event(
            name="Small Event", description="Test", venue="Test",
            capacity=1, event_date="2025-12-31",
        )
        event_id = event_result["event"]["id"]
        
        # Fill capacity
        reg_service.register_participant(event_id, "Guest A", "a@test.com")
        
        # Add 3 to waitlist
        reg_service.register_participant(event_id, "Waiter 1", "w1@test.com")
        reg_service.register_participant(event_id, "Waiter 2", "w2@test.com")
        reg_service.register_participant(event_id, "Waiter 3", "w3@test.com")
        
        # Cancel registration
        cancel_result = reg_service.cancel_registration(event_id, email="a@test.com")
        offer1_id = cancel_result["waitlist_offer"]["offer"]["id"]
        
        # Waiter 1 declines
        decline_result = offer_service.decline_offer(offer1_id)
        assert decline_result["success"] is True
        
        # Verify next offer was created for Waiter 2
        assert decline_result["next_offer"] is not None
        offer2_id = decline_result["next_offer"]["offer"]["id"]
        
        # Waiter 2 accepts
        accept_result = offer_service.accept_offer(offer2_id)
        assert accept_result["success"] is True
        
        # Verify Waiter 2 is confirmed
        db = Database()
        w2_participant = db.get_participant_by_email("w2@test.com")
        w2_reg = db.find_registration(event_id, w2_participant.id)
        assert w2_reg is not None
        assert w2_reg.status == RegistrationStatus.CONFIRMED
    
    def test_capacity_increase_with_waitlist(self):
        """Test that increasing capacity allows promoting waitlisted people."""
        event_service = EventService()
        reg_service = RegistrationService()
        offer_service = OfferService()
        
        # Create event with capacity 2
        event_result = event_service.create_event(
            name="Growing Event", description="Test", venue="Test",
            capacity=2, event_date="2025-12-31",
        )
        event_id = event_result["event"]["id"]
        
        # Fill and waitlist
        reg_service.register_participant(event_id, "A", "a@test.com")
        reg_service.register_participant(event_id, "B", "b@test.com")
        reg_service.register_participant(event_id, "C", "c@test.com")
        
        # Increase capacity
        update_result = event_service.update_capacity(event_id, 5)
        assert update_result["success"] is True
        assert update_result["promotions_available"] == 3
        
        # Event should now be OPEN
        event_data = event_service.get_event(event_id)
        assert event_data["status"] == EventStatus.OPEN
    
    def test_prevent_over_registration(self):
        """Ensure the system never exceeds capacity through any code path."""
        event_service = EventService()
        reg_service = RegistrationService()
        db = Database()
        
        event_result = event_service.create_event(
            name="Strict Capacity", description="Test", venue="Test",
            capacity=3, event_date="2025-12-31",
        )
        event_id = event_result["event"]["id"]
        
        # Register exactly to capacity
        for i in range(3):
            result = reg_service.register_participant(
                event_id, f"Guest {i}", f"guest{i}@test.com"
            )
            assert result["type"] == "CONFIRMED"
        
        # Attempt 10 more registrations
        for i in range(3, 13):
            result = reg_service.register_participant(
                event_id, f"Guest {i}", f"guest{i}@test.com"
            )
            assert result["type"] == "WAITLISTED"
        
        # Verify confirmed count never exceeds capacity
        confirmed_count = db.get_active_registration_count(event_id)
        assert confirmed_count == 3
    
    def test_event_cancellation_cleanup(self):
        """Test that cancelling an event properly cleans up everything."""
        event_service = EventService()
        reg_service = RegistrationService()
        db = Database()
        
        event_result = event_service.create_event(
            name="Doomed Event", description="Test", venue="Test",
            capacity=2, event_date="2025-12-31",
        )
        event_id = event_result["event"]["id"]
        
        reg_service.register_participant(event_id, "A", "a@test.com")
        reg_service.register_participant(event_id, "B", "b@test.com")
        reg_service.register_participant(event_id, "C", "c@test.com")
        
        cancel_result = event_service.cancel_event(event_id)
        assert cancel_result["success"] is True
        assert cancel_result["cancelled_registrations"] == 2
        assert cancel_result["cancelled_waitlist"] == 1
        
        # Verify event status
        event = db.get_event(event_id)
        assert event.status == EventStatus.CANCELLED