"""Member accounts, login and role checks (in-memory, demo grade)."""
import re
import secrets
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from storage.database import db
from config import RegistrationStatus

ORGANIZER = {"name": "Gild Tesoro", "email": "gild@tesoro.sea", "password": "Gold1234"}
MEMBERS = {}
TOKENS = {}

MEMBERS[ORGANIZER["email"]] = {
    "name": ORGANIZER["name"], "email": ORGANIZER["email"],
    "pw": generate_password_hash(ORGANIZER["password"]),
    "role": "organizer", "affiliation": "Tesoro Corporation",
}

EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ORG_RULES = [
    ("POST", re.compile(r"^/api/events$")),
    ("PUT", re.compile(r"^/api/events/[^/]+(/capacity)?$")),
    ("POST", re.compile(r"^/api/events/[^/]+/(close|cancel)$")),
    ("POST", re.compile(r"^/api/events/[^/]+/waitlist/remove$")),
]
REG_RX = re.compile(r"^/api/events/[^/]+/(register|cancel-registration)$")
OFFER_RX = re.compile(r"^/api/offers/([^/]+)/(accept|decline)$")


def _public(m):
    return {k: m[k] for k in ("name", "email", "role", "affiliation")}


def _me():
    h = request.headers.get("Authorization", "")
    if h.startswith("Bearer "):
        email = TOKENS.get(h[7:])
        return MEMBERS.get(email) if email else None
    return None


def _err(msg, code):
    return jsonify({"success": False, "error": msg}), code


def _mine(pid, email):
    p = db.get_participant(pid)
    return bool(p) and (getattr(p, "email", "") or "").lower() == email


def _offer_owner(offer_id):
    for ev in db.get_all_events():
        for o in db.get_pending_offers_for_event(ev.id):
            if getattr(o, "id", None) == offer_id:
                p = db.get_participant(o.participant_id)
                return (p.email or "").lower() if p else None
    return None


def register_auth(app):
    @app.before_request
    def guard():
        path, me = request.path, _me()
        for method, rx in ORG_RULES:
            if request.method == method and rx.match(path):
                if not me or me["role"] != "organizer":
                    return _err("Only the event organizer can do that. Sign in as an organizer.", 403)
                return None
        if request.method == "POST" and REG_RX.match(path):
            if not me:
                return _err("Sign in to reserve a seat.", 401)
            if me["role"] != "organizer":
                data = request.get_json(silent=True) or {}
                if (data.get("email") or "").strip().lower() != me["email"]:
                    return _err("Members can only manage their own seat.", 403)
        m = OFFER_RX.match(path)
        if request.method == "POST" and m:
            if not me:
                return _err("Sign in to answer this offer.", 401)
            if me["role"] != "organizer":
                owner = _offer_owner(m.group(1))
                if owner and owner != me["email"]:
                    return _err("This offer belongs to another guest.", 403)
        return None

    def _issue(m):
        tok = secrets.token_urlsafe(24)
        TOKENS[tok] = m["email"]
        return jsonify({"success": True, "token": tok, "member": _public(m)})

    @app.route("/api/auth/signup", methods=["POST"])
    def signup():
        d = request.get_json(silent=True) or {}
        name = (d.get("name") or "").strip()
        email = (d.get("email") or "").strip().lower()
        pw = d.get("password") or ""
        if len(name) < 2:
            return _err("Enter your name.", 400)
        if not EMAIL_RX.match(email):
            return _err("Enter a valid email address.", 400)
        if len(pw) < 6:
            return _err("Password needs at least 6 characters.", 400)
        if email in MEMBERS:
            return _err("That address is already on the crew list. Sign in instead.", 409)
        MEMBERS[email] = {"name": name, "email": email, "pw": generate_password_hash(pw),
                          "role": "member", "affiliation": d.get("affiliation") or "Independent"}
        return _issue(MEMBERS[email])

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        d = request.get_json(silent=True) or {}
        m = MEMBERS.get((d.get("email") or "").strip().lower())
        if not m or not check_password_hash(m["pw"], d.get("password") or ""):
            return _err("Wrong email or password.", 401)
        return _issue(m)

    @app.route("/api/auth/me", methods=["GET"])
    def me():
        m = _me()
        if not m:
            return _err("Not signed in.", 401)
        return jsonify({"success": True, "member": _public(m)})

    @app.route("/api/auth/logout", methods=["POST"])
    def logout():
        h = request.headers.get("Authorization", "")
        TOKENS.pop(h[7:], None)
        return jsonify({"success": True})

    @app.route("/api/me/passes", methods=["GET"])
    def my_passes():
        m = _me()
        if not m:
            return _err("Sign in first.", 401)
        email = m["email"]
        out = {"success": True, "seats": [], "waitlist": [], "offers": []}
        for ev in db.get_all_events():
            info = {"id": ev.id, "name": ev.name, "venue": ev.venue,
                    "date": ev.event_date, "status": ev.status}
            for reg in db.get_event_registrations(ev.id, status=RegistrationStatus.CONFIRMED):
                if _mine(reg.participant_id, email):
                    out["seats"].append({"event": info, "registration": reg.to_dict()})
            for w in db.get_event_waitlist(ev.id):
                if _mine(w.participant_id, email):
                    out["waitlist"].append({"event": info, "entry": w.to_dict()})
            for o in db.get_pending_offers_for_event(ev.id):
                if _mine(o.participant_id, email):
                    out["offers"].append({"event": info, "offer": o.to_dict()})
        return jsonify(out)