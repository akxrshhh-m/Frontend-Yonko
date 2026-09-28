"""
Gran Tesoro RSVP - Server & Smart Image Backend
Automatically detects and serves luffy, zoro, nami photos regardless of file extension.
"""
import os
import sys
import time
import uuid
import threading
import webbrowser
from datetime import datetime, timedelta
from flask import Flask, send_from_directory, jsonify, request

app = Flask(__name__, static_folder="static")

# Serve the static website
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# SMART IMAGE ROUTER (Fixes Windows hidden extensions)
@app.route("/img/<char_name>")
def serve_smart_image(char_name):
    static_dir = os.path.join(app.root_path, "static")
    if os.path.exists(static_dir):
        for filename in os.listdir(static_dir):
            if filename.lower().startswith(char_name.lower()) and filename.lower() != "index.html":
                return send_from_directory(static_dir, filename)
    return "Image not found", 404

# Serve regular static files
@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

# In-Memory Backend Data
def gen_id(prefix="GT"):
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

EVENTS = {}
REGISTRATIONS = {}
WAITLIST = {}
OFFERS = {}
AUDIT = []

def log(action, details):
    AUDIT.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "action": action, "details": details})

def vip_tier(num, cap):
    r = num / cap if cap > 0 else 1
    if r <= 0.25: return "Celestial Dragon Tier (Ultra VIP)"
    if r <= 0.5: return "Admiral Tier (Premium VIP)"
    return "Captain Tier (Standard VIP)"

def rank_title(pos):
    if pos == 1: return "Yonko-Level Priority"
    if pos <= 3: return "Warlord-Level Priority"
    return "Supernova-Level Priority"

def seed():
    EVENTS.clear(); REGISTRATIONS.clear(); WAITLIST.clear(); OFFERS.clear(); AUDIT.clear()

    e1 = {"id": "GT-EVT-TESORO", "name": "Gran Tesoro VIP Golden Gala",
          "description": "Gild Tesoro's exclusive 24K casino banquet aboard the golden ship.",
          "venue": "Gran Tesoro - Gold Casino Ship", "capacity": 4,
          "event_date": "2025-12-31 20:00", "status": "OPEN",
          "organizer": "Gild Tesoro's Golden Entertainment Division", "category": "VIP Gala",
          "created_at": now_iso(), "updated_at": now_iso()}
    EVENTS[e1["id"]] = e1

    e2 = {"id": "GT-EVT-REVERIE", "name": "World Government Reverie Summit",
          "description": "Sacred council at Marijoa where 50 kingdom rulers gather.",
          "venue": "Sacred Marijoa - Pangaea Castle", "capacity": 6,
          "event_date": "2026-07-14 10:00", "status": "OPEN",
          "organizer": "The Five Elders (Gorosei)", "category": "Council Session",
          "created_at": now_iso(), "updated_at": now_iso()}
    EVENTS[e2["id"]] = e2

    e3 = {"id": "GT-EVT-BARATIE", "name": "Baratie All-Blue Chef's Table",
          "description": "Sanji and Zeff's ocean gourmet feast.",
          "venue": "Baratie Floating Restaurant - East Blue", "capacity": 3,
          "event_date": "2025-08-20 19:00", "status": "OPEN",
          "organizer": "Chef Zeff & Fighting Cooks", "category": "Banquet",
          "created_at": now_iso(), "updated_at": now_iso()}
    EVENTS[e3["id"]] = e3

    # Confirmed guests
    guests = [
        ("Monkey D. Luffy", "luffy@strawhat.com", "Straw Hat Pirates"),
        ("Roronoa Zoro", "zoro@strawhat.com", "Straw Hat Pirates"),
        ("Nami", "nami@strawhat.com", "Straw Hat Pirates"),
        ("Boa Hancock", "hancock@kuja.com", "Kuja Pirates"),
    ]
    for i, (n, em, af) in enumerate(guests, 1):
        pid = gen_id("PAR"); rid = gen_id("REG")
        REGISTRATIONS[rid] = {
            "id": rid, "event_id": e1["id"], "participant_id": pid,
            "status": "CONFIRMED", "registration_number": i,
            "vip_tier": vip_tier(i, 4), "registered_at": now_iso(),
            "_participant": {"id": pid, "name": n, "email": em, "affiliation": af}
        }

    # Waitlisted guests
    for i, (n, em, af) in enumerate([
        ("Vinsmoke Sanji", "sanji@germa.com", "Straw Hat Pirates"),
        ("Trafalgar Law", "law@heart.com", "Heart Pirates")
    ], 1):
        pid = gen_id("PAR"); wid = gen_id("WL")
        WAITLIST[wid] = {
            "id": wid, "event_id": e1["id"], "participant_id": pid,
            "position": i, "rank_title": rank_title(i),
            "is_active": True, "added_at": now_iso(),
            "_participant": {"id": pid, "name": n, "email": em, "affiliation": af}
        }

    log("SYSTEM_INIT", "Gran Tesoro loaded with voyages and demo guests.")

seed()

def confirmed_for(eid):
    return [r for r in REGISTRATIONS.values() if r["event_id"] == eid and r["status"] == "CONFIRMED"]

def waitlist_for(eid):
    return sorted([w for w in WAITLIST.values() if w["event_id"] == eid and w["is_active"]], key=lambda x: x["position"])

def event_stats(eid):
    c = len(confirmed_for(eid))
    ev = EVENTS.get(eid, {})
    cap = ev.get("capacity", 4)
    return {"confirmed_registrations": c, "available_seats": max(0, cap - c),
            "waitlist_count": len(waitlist_for(eid)), "is_full": c >= cap}

# API Routes
@app.route("/api/events", methods=["GET"])
def list_events():
    out = [dict(ev, stats=event_stats(ev["id"])) for ev in EVENTS.values()]
    return jsonify({"success": True, "events": out, "count": len(out)})

@app.route("/api/events", methods=["POST"])
def create_event():
    d = request.get_json() or {}
    eid = gen_id("EVT")
    EVENTS[eid] = {
        "id": eid, "name": d.get("name",""), "description": d.get("description",""),
        "venue": d.get("venue",""), "capacity": int(d.get("capacity",4)),
        "event_date": d.get("event_date",""), "status": "OPEN",
        "organizer": d.get("organizer","Gild Tesoro"), "category": d.get("category","VIP Gala"),
        "created_at": now_iso(), "updated_at": now_iso()
    }
    log("EVENT_CREATED", f"Voyage '{EVENTS[eid]['name']}' chartered.")
    return jsonify({"success": True, "message": "Voyage chartered!", "event": EVENTS[eid]}), 201

@app.route("/api/events/<eid>", methods=["GET"])
def get_event(eid):
    ev = EVENTS.get(eid)
    if not ev: return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True, "event": dict(ev, stats=event_stats(eid))})

@app.route("/api/events/<eid>/summary", methods=["GET"])
def summary(eid):
    ev = EVENTS.get(eid)
    if not ev: return jsonify({"success": False, "error": "Not found"}), 404
    conf = confirmed_for(eid)
    wl = waitlist_for(eid)
    offers = [o for o in OFFERS.values() if o["event_id"] == eid and o["status"] == "PENDING"]
    return jsonify({
        "event": ev,
        "stats": {**event_stats(eid), "confirmed_count": len(conf), "capacity": ev["capacity"], "pending_offers": len(offers)},
        "confirmed_guests": [{"registration": {k:v for k,v in r.items() if k!="_participant"}, "participant": r["_participant"]} for r in conf],
        "waitlist_guests": [{"waitlist_entry": {k:v for k,v in w.items() if k!="_participant"}, "participant": w["_participant"]} for w in wl],
        "pending_offers": offers
    })

@app.route("/api/events/<eid>/register", methods=["POST"])
def register(eid):
    ev = EVENTS.get(eid)
    if not ev: return jsonify({"success": False, "message": "Event not found"}), 404
    d = request.get_json() or {}
    name = d.get("name","").strip()
    email = d.get("email","").strip().lower()
    aff = d.get("affiliation","Independent")

    conf = confirmed_for(eid)
    if len(conf) < ev["capacity"]:
        pid = gen_id("PAR"); rid = gen_id("REG")
        num = len(conf) + 1
        REGISTRATIONS[rid] = {
            "id": rid, "event_id": eid, "participant_id": pid, "status": "CONFIRMED",
            "registration_number": num, "vip_tier": vip_tier(num, ev["capacity"]),
            "registered_at": now_iso(), "_participant": {"id": pid, "name": name, "email": email, "affiliation": aff}
        }
        log("RSVP_CONFIRMED", f"{name} claimed Seat #{num}.")
        return jsonify({"success": True, "type": "CONFIRMED", "message": f"Welcome to the Gold Room, {name}!"})
    else:
        pid = gen_id("PAR"); wid = gen_id("WL")
        pos = len(waitlist_for(eid)) + 1
        WAITLIST[wid] = {
            "id": wid, "event_id": eid, "participant_id": pid, "position": pos,
            "rank_title": rank_title(pos), "is_active": True, "added_at": now_iso(),
            "_participant": {"id": pid, "name": name, "email": email, "affiliation": aff}
        }
        log("WAITLISTED", f"{name} placed on deck at position #{pos}.")
        return jsonify({"success": True, "type": "WAITLISTED", "message": f"Gold Room full! {name} waits on deck at #{pos}."})

@app.route("/api/events/<eid>/cancel-registration", methods=["POST"])
def cancel(eid):
    d = request.get_json() or {}
    email = d.get("email","").strip().lower()
    reg = next((r for r in REGISTRATIONS.values() if r["event_id"]==eid and r.get("_participant",{}).get("email")==email and r["status"]=="CONFIRMED"), None)
    if not reg: return jsonify({"success": False, "message": "No active seat found."}), 404
    reg["status"] = "CANCELLED"
    p = reg.get("_participant", {})
    log("CANCELLATION", f"{p.get('name','?')} abandoned ship.")

    wl = waitlist_for(eid)
    if wl:
        nxt = wl[0]; oid = gen_id("OFR")
        OFFERS[oid] = {
            "id": oid, "event_id": eid, "participant_id": nxt["participant_id"],
            "waitlist_entry_id": nxt["id"], "status": "PENDING", "created_at": now_iso(),
            "expires_at": (datetime.utcnow()+timedelta(seconds=60)).isoformat()+"Z",
            "time_remaining_seconds": 60, "participant": nxt.get("_participant", {})
        }
        log("OFFER_SENT", f"Den Den Mushi ringing for {nxt.get('_participant',{}).get('name','?')}!")
        return jsonify({"success": True, "message": "Seat freed! Den Den Mushi calling next guest.",
                        "waitlist_offer": {"success": True, "offer": OFFERS[oid], "participant": nxt.get("_participant",{})}})
    return jsonify({"success": True, "message": "Seat cancelled. Deck is clear."})

@app.route("/api/offers/<oid>/accept", methods=["POST"])
def accept(oid):
    o = OFFERS.get(oid)
    if not o or o["status"] != "PENDING":
        return jsonify({"success": False, "message": "Offer expired or invalid."}), 400
    o["status"] = "ACCEPTED"
    wl = WAITLIST.get(o["waitlist_entry_id"])
    if wl: wl["is_active"] = False
    ev = EVENTS.get(o["event_id"])
    conf = confirmed_for(o["event_id"])
    num = len(conf) + 1
    p = o.get("participant", {})
    rid = gen_id("REG")
    REGISTRATIONS[rid] = {
        "id": rid, "event_id": o["event_id"], "participant_id": o["participant_id"], "status": "CONFIRMED",
        "registration_number": num, "vip_tier": vip_tier(num, ev["capacity"] if ev else 4),
        "registered_at": now_iso(), "_participant": p
    }
    for i, w in enumerate(waitlist_for(o["event_id"]), 1):
        w["position"] = i; w["rank_title"] = rank_title(i)
    log("OFFER_ACCEPTED", f"{p.get('name','?')} accepted the seat!")
    return jsonify({"success": True, "message": f"Welcome to the Gold Room, {p.get('name','?')}!"})

@app.route("/api/offers/<oid>/decline", methods=["POST"])
def decline(oid):
    o = OFFERS.get(oid)
    if not o or o["status"] != "PENDING":
        return jsonify({"success": False, "message": "Offer not found."}), 400
    o["status"] = "DECLINED"
    wl = WAITLIST.get(o["waitlist_entry_id"])
    if wl: wl["is_active"] = False
    return jsonify({"success": True, "message": "Offer passed to next in line."})

# Fallback auth endpoints
@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    return jsonify({"success": True, "member": {"name": "Gild Tesoro", "email": "gild@tesoro.sea", "role": "organizer"}})

@app.route("/api/me/passes", methods=["GET"])
def my_passes():
    return jsonify({"success": True, "seats": [], "waitlist": [], "offers": []})

def open_browser():
    time.sleep(1.0)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    print("\n🏆 Gran Tesoro RSVP Server running at http://127.0.0.1:5000\n")
    app.run(port=5000, debug=False)