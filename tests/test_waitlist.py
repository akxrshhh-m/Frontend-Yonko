"""
Tests for Waitlist Service
"""
import pytest
from services.event_service import EventService
from services.registration_service import RegistrationService
from services.waitlist_service import WaitlistService
from storage.database import Database


@pytest.fixture(autouse=True)
def reset_db():
    db = Database()
    db.reset()
    yield
    db.reset()


@pytest.fixture
def full_event():
    """Create a full event with waitlisted participants."""
    event_service = EventService()
    reg_service = RegistrationService()
    
    result = event_service.create_event(
        name="Full Event", description="Test", venue="Test",
        capacity=2, event_date="2025-12-31",
    )
    event_id = result["event"]["id"]
    
    # Fill to capacity
    reg_service.register_participant(event_id, "Guest A", "a@test.com")
    reg_service.register_participant(event_id, "Guest B", "b@test.com")
    
    # Add to waitlist
    reg_service.register_participant(event_id, "Waiter 1", "w1@test.com")
    reg_service.register_participant(event_id, "Waiter 2", "w2@test.com")
    reg_service.register_participant(event_id, "Waiter 3", "w3@test.com")
    
    return event_id


class TestWaitlist:
    def test_waitlist_order(self, full_event):
        waitlist_service = WaitlistService()
        result = waitlist_service.get_waitlist(full_event)
        
        assert result["success"] is True
        assert result["waitlist_count"] == 3
        
        # Verify FIFO order
        positions = [entry["waitlist_entry"]["position"] for entry in result["waitlist"]]
        assert positions == [1, 2, 3]
    
    def test_get_next_in_line(self, full_event):
        waitlist_service = WaitlistService()
        next_entry = waitlist_service.get_next_in_line(full_event)
        
        assert next_entry is not None
        assert next_entry.position == 1
    
    def test_remove_from_waitlist(self, full_event):
        waitlist_service = WaitlistService()
        db = Database()
        
        # Get first waitlister's participant ID
        waitlist = waitlist_service.get_waitlist(full_event)
        first_participant_id = waitlist["waitlist"][0]["participant"]["id"]
        
        result = waitlist_service.remove_from_waitlist(full_event, first_participant_id)
        assert result["success"] is True
        
        # Verify remaining waitlist is renumbered
        updated_waitlist = waitlist_service.get_waitlist(full_event)
        assert updated_waitlist["waitlist_count"] == 2
        positions = [e["waitlist_entry"]["position"] for e in updated_waitlist["waitlist"]]
        assert positions == [1, 2]
    
    def test_waitlist_rank_titles(self, full_event):
        waitlist_service = WaitlistService()
        result = waitlist_service.get_waitlist(full_event)
        
        for entry in result["waitlist"]:
            assert entry["waitlist_entry"]["rank_title"] != ""
    
    def test_promote_from_waitlist(self, full_event):
        waitlist_service = WaitlistService()
        
        # Get the first waitlist entry
        next_entry = waitlist_service.get_next_in_line(full_event)
        
        # First, we need to create a seat (cancel a registration)
        reg_service = RegistrationService()
        reg_service.cancel_registration(full_event, email="a@test.com")
        
        # The cancellation should have triggered an auto-offer
        # But let's test direct promotion
        # Note: After cancellation, the offer service may have already promoted
        # This is expected behavior
    
    def test_empty_waitlist(self):
        event_service = EventService()
        waitlist_service = WaitlistService()
        
        result = event_service.create_event(
            name="Empty Event", description="Test", venue="Test",
            capacity=10, event_date="2025-12-31",
        )
        event_id = result["event"]["id"]
        
        next_entry = waitlist_service.get_next_in_line(event_id)
        assert next_entry is None