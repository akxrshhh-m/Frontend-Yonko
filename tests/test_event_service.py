"""
Tests for Event Service
"""
import pytest
from services.event_service import EventService
from storage.database import Database
from config import EventStatus
from utils.validators import ValidationError


@pytest.fixture(autouse=True)
def reset_db():
    """Reset database before each test."""
    db = Database()
    db.reset()
    yield
    db.reset()


@pytest.fixture
def event_service():
    return EventService()


class TestCreateEvent:
    def test_create_event_success(self, event_service):
        result = event_service.create_event(
            name="Gran Tesoro Gala",
            description="A golden evening",
            venue="Gran Tesoro Ship",
            capacity=100,
            event_date="2025-12-31 20:00",
        )
        assert result["success"] is True
        assert result["event"]["name"] == "Gran Tesoro Gala"
        assert result["event"]["capacity"] == 100
        assert result["event"]["status"] == EventStatus.OPEN
    
    def test_create_event_missing_name(self, event_service):
        with pytest.raises(ValidationError):
            event_service.create_event(
                name="",
                description="Test",
                venue="Test Venue",
                capacity=10,
                event_date="2025-12-31",
            )
    
    def test_create_event_invalid_capacity(self, event_service):
        with pytest.raises(ValidationError):
            event_service.create_event(
                name="Test Event",
                description="Test",
                venue="Test Venue",
                capacity=-5,
                event_date="2025-12-31",
            )
    
    def test_create_event_zero_capacity(self, event_service):
        with pytest.raises(ValidationError):
            event_service.create_event(
                name="Test Event",
                description="Test",
                venue="Test Venue",
                capacity=0,
                event_date="2025-12-31",
            )


class TestGetEvent:
    def test_get_event_with_stats(self, event_service):
        create_result = event_service.create_event(
            name="Test Event",
            description="Test",
            venue="Test Venue",
            capacity=50,
            event_date="2025-12-31",
        )
        event_id = create_result["event"]["id"]
        
        result = event_service.get_event(event_id)
        assert result is not None
        assert result["stats"]["confirmed_registrations"] == 0
        assert result["stats"]["available_seats"] == 50
        assert result["stats"]["waitlist_count"] == 0
        assert result["stats"]["is_full"] is False
    
    def test_get_nonexistent_event(self, event_service):
        result = event_service.get_event("FAKE-ID")
        assert result is None


class TestUpdateCapacity:
    def test_increase_capacity(self, event_service):
        create_result = event_service.create_event(
            name="Test", description="Test", venue="Test",
            capacity=10, event_date="2025-12-31",
        )
        event_id = create_result["event"]["id"]
        
        result = event_service.update_capacity(event_id, 20)
        assert result["success"] is True
        assert result["old_capacity"] == 10
        assert result["new_capacity"] == 20
    
    def test_decrease_capacity_below_registrations(self, event_service):
        from services.registration_service import RegistrationService
        reg_service = RegistrationService()
        
        create_result = event_service.create_event(
            name="Test", description="Test", venue="Test",
            capacity=5, event_date="2025-12-31",
        )
        event_id = create_result["event"]["id"]
        
        # Register 3 participants
        for i in range(3):
            reg_service.register_participant(
                event_id, f"Guest {i}", f"guest{i}@test.com"
            )
        
        # Try to reduce capacity below 3
        with pytest.raises(ValidationError):
            event_service.update_capacity(event_id, 2)


class TestCloseAndCancelEvent:
    def test_close_event(self, event_service):
        create_result = event_service.create_event(
            name="Test", description="Test", venue="Test",
            capacity=10, event_date="2025-12-31",
        )
        event_id = create_result["event"]["id"]
        
        result = event_service.close_event(event_id)
        assert result["success"] is True
        assert result["event"]["status"] == EventStatus.CLOSED
    
    def test_cancel_event(self, event_service):
        from services.registration_service import RegistrationService
        reg_service = RegistrationService()
        
        create_result = event_service.create_event(
            name="Test", description="Test", venue="Test",
            capacity=10, event_date="2025-12-31",
        )
        event_id = create_result["event"]["id"]
        
        reg_service.register_participant(event_id, "Guest 1", "guest1@test.com")
        
        result = event_service.cancel_event(event_id)
        assert result["success"] is True
        assert result["cancelled_registrations"] == 1