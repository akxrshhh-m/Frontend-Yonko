"""
REST API Routes - Gran Tesoro RSVP System
Flask-based API endpoints.
"""
import os
from flask import Flask, request, jsonify, send_from_directory
from services.event_service import EventService
from services.registration_service import RegistrationService
from services.waitlist_service import WaitlistService
from services.offer_service import OfferService
from storage.database import db
from utils.validators import ValidationError
from api.auth import register_auth


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    event_service = EventService()
    registration_service = RegistrationService()
    waitlist_service = WaitlistService()
    offer_service = OfferService()
    
    # ---- Error Handlers ----
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({"success": False, "error": e.message, "field": e.field}), 400
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Resource not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal server error"}), 500
        # ---- Frontend ----
    STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))

    @app.route("/")
    def home():
        return send_from_directory(STATIC_DIR, "index.html")

    @app.route("/media/<path:name>")
    def media(name):
        return send_from_directory(STATIC_DIR, name)

    # ---- Health Check ----
    # ---- Health Check ----
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "online",
            "system": "Gran Tesoro VIP Gala & Reverie Summit RSVP",
            "message": "The golden city awaits! 🏆"
        })
    
    # ==========================================
    # EVENT ENDPOINTS
    # ==========================================
    
    @app.route("/api/events", methods=["POST"])
    def create_event():
        """Create a new event."""
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400
        
        try:
            result = event_service.create_event(
                name=data.get("name", ""),
                description=data.get("description", ""),
                venue=data.get("venue", ""),
                capacity=data.get("capacity", 0),
                event_date=data.get("event_date", ""),
                organizer=data.get("organizer", "Gild Tesoro's Golden Entertainment Division"),
                category=data.get("category", "VIP Gala"),
            )
            return jsonify(result), 201 if result["success"] else 400
        except ValidationError as e:
            return jsonify({"success": False, "error": e.message, "field": e.field}), 400
    
    @app.route("/api/events", methods=["GET"])
    def list_events():
        """List all events."""
        status = request.args.get("status")
        events = event_service.list_events(status=status)
        return jsonify({"success": True, "events": events, "count": len(events)})
    
    @app.route("/api/events/<event_id>", methods=["GET"])
    def get_event(event_id):
        """Get event details."""
        result = event_service.get_event(event_id)
        if not result:
            return jsonify({"success": False, "error": "Event not found"}), 404
        return jsonify({"success": True, "event": result})
    
    @app.route("/api/events/<event_id>", methods=["PUT"])
    def update_event(event_id):
        """Update event details."""
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400
        
        try:
            result = event_service.update_event(event_id, **data)
            return jsonify(result), 200 if result["success"] else 400
        except ValidationError as e:
            return jsonify({"success": False, "error": e.message}), 400
    
    @app.route("/api/events/<event_id>/capacity", methods=["PUT"])
    def update_capacity(event_id):
        """Update event capacity."""
        data = request.get_json()
        if not data or "capacity" not in data:
            return jsonify({"success": False, "error": "Capacity field required"}), 400
        
        try:
            result = event_service.update_capacity(event_id, data["capacity"])
            return jsonify(result), 200 if result["success"] else 400
        except ValidationError as e:
            return jsonify({"success": False, "error": e.message}), 400
    
    @app.route("/api/events/<event_id>/close", methods=["POST"])
    def close_event(event_id):
        """Close an event."""
        result = event_service.close_event(event_id)
        return jsonify(result), 200 if result["success"] else 404
    
    @app.route("/api/events/<event_id>/cancel", methods=["POST"])
    def cancel_event(event_id):
        """Cancel an event."""
        result = event_service.cancel_event(event_id)
        return jsonify(result), 200 if result["success"] else 404
    
    @app.route("/api/events/<event_id>/summary", methods=["GET"])
    def event_summary(event_id):
        """Get comprehensive event summary."""
        result = event_service.get_event_summary(event_id)
        if not result:
            return jsonify({"success": False, "error": "Event not found"}), 404
        return jsonify({"success": True, **result})
    
    # ==========================================
    # REGISTRATION ENDPOINTS
    # ==========================================
    
    @app.route("/api/events/<event_id>/register", methods=["POST"])
    def register_participant(event_id):
        """Register a participant for an event."""
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400
        
        try:
            result = registration_service.register_participant(
                event_id=event_id,
                name=data.get("name", ""),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                affiliation=data.get("affiliation", "Independent"),
                auto_waitlist=data.get("auto_waitlist", True),
            )
            status_code = 201 if result.get("success") else 400
            if result.get("type") == "WAITLISTED" and result.get("success"):
                status_code = 202  # Accepted but waitlisted
            return jsonify(result), status_code
        except ValidationError as e:
            return jsonify({"success": False, "error": e.message}), 400
    
    @app.route("/api/events/<event_id>/cancel-registration", methods=["POST"])
    def cancel_registration(event_id):
        """Cancel a registration."""
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400
        
        result = registration_service.cancel_registration(
            event_id=event_id,
            participant_id=data.get("participant_id"),
            email=data.get("email"),
            registration_id=data.get("registration_id"),
        )
        return jsonify(result), 200 if result["success"] else 400
    
    @app.route("/api/events/<event_id>/registrations", methods=["GET"])
    def get_event_registrations(event_id):
        """Get all registrations for an event."""
        status = request.args.get("status")
        regs = db.get_event_registrations(event_id, status=status)
        registrations_data = []
        for reg in regs:
            participant = db.get_participant(reg.participant_id)
            registrations_data.append({
                "registration": reg.to_dict(),
                "participant": participant.to_dict() if participant else None,
            })
        return jsonify({"success": True, "registrations": registrations_data, "count": len(registrations_data)})
    
    # ==========================================
    # WAITLIST ENDPOINTS
    # ==========================================
    
    @app.route("/api/events/<event_id>/waitlist", methods=["GET"])
    def get_waitlist(event_id):
        """Get the waitlist for an event."""
        result = waitlist_service.get_waitlist(event_id)
        return jsonify(result), 200 if result["success"] else 404
    
    @app.route("/api/events/<event_id>/waitlist/remove", methods=["POST"])
    def remove_from_waitlist(event_id):
        """Remove a participant from the waitlist."""
        data = request.get_json()
        if not data or "participant_id" not in data:
            return jsonify({"success": False, "error": "participant_id required"}), 400
        
        result = waitlist_service.remove_from_waitlist(event_id, data["participant_id"])
        return jsonify(result), 200 if result["success"] else 400
    
    # ==========================================
    # OFFER ENDPOINTS
    # ==========================================
    
    @app.route("/api/offers/<offer_id>", methods=["GET"])
    def get_offer(offer_id):
        """Get offer status."""
        result = offer_service.get_offer_status(offer_id)
        return jsonify(result), 200 if result["success"] else 404
    
    @app.route("/api/offers/<offer_id>/accept", methods=["POST"])
    def accept_offer(offer_id):
        """Accept a seat offer."""
        result = offer_service.accept_offer(offer_id)
        return jsonify(result), 200 if result["success"] else 400
    
    @app.route("/api/offers/<offer_id>/decline", methods=["POST"])
    def decline_offer(offer_id):
        """Decline a seat offer."""
        result = offer_service.decline_offer(offer_id)
        return jsonify(result), 200 if result["success"] else 400
    
    @app.route("/api/offers/check-expired", methods=["POST"])
    def check_expired_offers():
        """Check and process expired offers."""
        event_id = request.args.get("event_id")
        result = offer_service.check_and_expire_offers(event_id)
        return jsonify(result)
    
    # ==========================================
    # PARTICIPANT ENDPOINTS
    # ==========================================
    
    @app.route("/api/participants/<participant_id>/registrations", methods=["GET"])
    def get_participant_registrations(participant_id):
        """Get all registrations for a participant."""
        result = registration_service.get_participant_registrations(participant_id=participant_id)
        return jsonify(result), 200 if result["success"] else 404
    
    @app.route("/api/participants/by-email", methods=["GET"])
    def get_participant_by_email():
        """Get participant registrations by email."""
        email = request.args.get("email")
        if not email:
            return jsonify({"success": False, "error": "email parameter required"}), 400
        result = registration_service.get_participant_registrations(email=email)
        return jsonify(result), 200 if result["success"] else 404
    
    # ==========================================
    # AUDIT LOG
    # ==========================================
    
    @app.route("/api/audit-log", methods=["GET"])
    def get_audit_log():
        """Get audit log entries."""
        entity_id = request.args.get("entity_id")
        limit = request.args.get("limit", 50, type=int)
        logs = db.get_audit_log(entity_id=entity_id, limit=limit)
        return jsonify({"success": True, "logs": logs, "count": len(logs)})
    
    register_auth(app)

    return app