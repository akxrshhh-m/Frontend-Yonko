"""
Tests for Registration Service
"""
import pytest
from services.event_service import EventService
from services.registration_service import RegistrationService
from storage.database import Database
from config import RegistrationStatus


@pytest.fixture(autouse=True)
def reset_db():
    db = Database()
    db.reset()
    yield
    db.reset()


@pytest.fixture
def services():
    event_service = EventService()
    reg_service = RegistrationService()
    
    # Create a test event with capacity 3
    result = event_service.create_event(
        name="Test Gala", description="Test", venue="Test Venue",
        capacity=3, event_date="2025-12-31",
    )
    event_id = result["event"]["id"]
    
    return {
        "event_service": event_service,
        "reg_service": reg_service,
        "event_id": event_id,
    }


class TestRegistration:
    def test_successful_registration(self, services):
        result = services["reg_service"].register_participant(
            services["event_id"], "Luffy", "luffy@strawhat.com",
            affiliation="Straw Hat Pirates"
        )
        assert result["success"] is True
        assert result["type"] == "CONFIRMED"
        assert result["registration"]["status"] == RegistrationStatus.CONFIRMED
    
    def test_registration_assigns_vip_tier(self, services):
        result = services["reg_service"].register_participant(
            services["event_id"], "Luffy", "luffy@strawhat.com"
        )
        assert "vip_tier" in result
        assert result["vip_tier"] != ""
    
    def test_prevent_duplicate_registration(self, services):
        services["reg_service"].register_participant(
            services["event_id"], "Luffy", "luffy@strawhat.com"
        )
        result = services["reg_service"].register_participant(
            services["event_id"], "Luffy", "luffy@strawhat.com"
        )
        assert result["success"] is False
        assert result["code"] == "ALREADY_REGISTERED"
    
    def test_capacity_enforcement(self, services):
        """Register up to capacity, then verify 4th is waitlisted."""
        for i in range(3):
            result = services["reg_service"].register_participant(
                services["event_id"], f"Guest {i}", f"guest{i}@test.com"
            )
            assert result["success"] is True
            assert result["type"] == "CONFIRMED"
        
        # 4th registration should be waitlisted
        result = services["reg_service"].register_participant(
            services["event_id"], "Guest 3", "guest3@test.com"
        )
        assert result["success"] is True
        assert result["type"] == "WAITLISTED"
    
    def test_registration_on_closed_event(self, services):
        services["event_service"].close_event(services["event_id"])
        result = services["reg_service"].register_participant(
            services["event_id"], "Luffy", "luffy@strawhat.com"
        )
        assert result["success"] is False
        assert result["code"] == "EVENT_CLOSED"
    
    def test_registration_nonexistent_event(self, services):
        result = services["reg_service"].register_participant(
            "FAKE-EVENT", "Luffy", "luffy@strawhat.com"
        )
        assert result["success"] is False
        assert result["code"] == "EVENT_NOT_FOUND"


class TestCancellation:
    def test_cancel_registration(self, services):
        reg_result = services["reg_service"].register_participant(
            services["event_id"], "Luffy", "luffy@strawhat.com"
        )
        
        cancel_result = services["reg_service"].cancel_registration(
            services["event_id"], email="luffy@strawhat.com"
        )
        assert cancel_result["success"] is True
    
    def test_cancel_already_cancelled(self, services):
        services["reg_service"].register_participant(
            services["event_id"], "Luffy", "luffy@strawhat.com"
        )
        services["reg_service"].cancel_registration(
            services["event_id"], email="luffy@strawhat.com"
        )
        
        result = services["reg_service"].cancel_registration(
            services["event_id"], email="luffy@strawhat.com"
        )
        assert result["success"] is False
        assert result["code"] == "ALREADY_CANCELLED"
    
    def test_cancel_nonexistent_registration(self, services):
        result = services["reg_service"].cancel_registration(
            services["event_id"], email="nobody@test.com"
        )
        assert result["success"] is False
    
    def test_cancellation_triggers_waitlist_offer(self, services):
        """Register to capacity, add waitlister, cancel one, verify offer is created."""
        for i in range(3):
            services["reg_service"].register_participant(
                services["event_id"], f"Guest {i}", f"guest{i}@test.com"
            )
        
        # Waitlist someone
        services["reg_service"].register_participant(
            services["event_id"], "Waitlisted", "waitlisted@test.com"
        )
        
        # Cancel one registration
        result = services["reg_service"].cancel_registration(
            services["event_id"], email="guest0@test.com"
        )
        
        assert result["success"] is True
        assert "waitlist_offer" in result
        assert result["waitlist_offer"]["success"] is True