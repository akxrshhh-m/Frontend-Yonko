"""
Gran Tesoro VIP Gala & Reverie Summit - Full Visual Web Application
Serves the complete interactive frontend with real-time REST API backend.
"""
import os
import sys
import time
import uuid
import webbrowser
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# ==============================================================================
# IN-MEMORY DATABASE & STATE MACHINE
# ==============================================================================
def gen_id(prefix="GT"):
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"

EVENTS = {
    "evt_tesoro": {
        "id": "evt_tesoro",
        "name": "Gran Tesoro VIP Golden Gala",
        "tagline": "Gild Tesoro's Exclusive 24K Casino Banquet",
        "venue": "Gran Tesoro - VIP Gold Casino Ship",
        "date": "December 31, 2025 • 20:00 JST",
        "capacity": 4,
        "organizer": "Gild Tesoro's Golden Entertainment Division",
        "theme_color": "gold"
    },
    "evt_reverie": {
        "id": "evt_reverie",
        "name": "World Government Reverie Summit",
        "tagline": "The Sacred 50-Kingdom High Council",
        "venue": "Sacred Marijoa - Pangaea Castle",
        "date": "July 14, 2026 • 10:00 JST",
        "capacity": 5,
        "organizer": "The Five Elders (Gorosei)",
        "theme_color": "crimson"
    },
    "evt_baratie": {
        "id": "evt_baratie",
        "name": "Baratie All-Blue Chef's Table",
        "tagline": "Sanji & Zeff's Ocean Gourmet Feast",
        "venue": "Baratie Floating Restaurant - East Blue",
        "date": "August 20, 2025 • 19:00 JST",
        "capacity": 3,
        "organizer": "Chef Zeff & Fighting Cooks",
        "theme_color": "cyan"
    }
}

ACTIVE_EVENT_ID = "evt_tesoro"
REGISTRATIONS = {}   # id -> dict
WAITLIST = {}        # id -> dict
OFFERS = {}          # id -> dict
AUDIT_LOGS = []

def log_audit(action, details):
    AUDIT_LOGS.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "details": details
    })

def get_vip_tier(num, cap):
    ratio = num / cap if cap > 0 else 1
    if ratio <= 0.25:
        return "👑 Celestial Dragon (Ultra VIP)"
    elif ratio <= 0.5:
        return "⚔️ Admiral VIP"
    return "🏴‍☠️ Pirate Captain Tier"

def get_rank_title(pos):
    if pos == 1:
        return "🔥 Yonko Priority (#1 in Queue)"
    elif pos <= 3:
        return "⚡ Warlord Priority"
    return "🌊 Supernova Priority"

def seed_sample_data():
    global REGISTRATIONS, WAITLIST, OFFERS
    REGISTRATIONS.clear()
    WAITLIST.clear()
    OFFERS.clear()
    
    # 4 confirmed guests (Full Capacity for Tesoro)
    sample_confirmed = [
        ("Monkey D. Luffy", "luffy@strawhat.com", "Straw Hat Pirates", "3,000,000,000 ฿"),
        ("Roronoa Zoro", "zoro@strawhat.com", "Straw Hat Pirates", "1,111,000,000 ฿"),
        ("Nami", "nami@strawhat.com", "Straw Hat Pirates", "366,000,000 ฿"),
        ("Boa Hancock", "hancock@kuja.com", "Kuja Pirates / Empress", "1,659,000,000 ฿"),
    ]
    for idx, (name, email, affil, bounty) in enumerate(sample_confirmed, 1):
        rid = gen_id("REG")
        REGISTRATIONS[rid] = {
            "id": rid,
            "event_id": "evt_tesoro",
            "name": name,
            "email": email,
            "affiliation": affil,
            "bounty": bounty,
            "seat_number": idx,
            "vip_tier": get_vip_tier(idx, 4),
            "status": "CONFIRMED",
            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    # 2 waitlisted guests
    sample_waitlist = [
        ("Vinsmoke Sanji", "sanji@germa.com", "Straw Hat Pirates", "1,032,000,000 ฿"),
        ("Trafalgar D. Law", "law@heart.com", "Heart Pirates", "3,000,000,000 ฿")
    ]
    for idx, (name, email, affil, bounty) in enumerate(sample_waitlist, 1):
        wid = gen_id("WL")
        WAITLIST[wid] = {
            "id": wid,
            "event_id": "evt_tesoro",
            "name": name,
            "email": email,
            "affiliation": affil,
            "bounty": bounty,
            "position": idx,
            "rank_title": get_rank_title(idx),
            "is_active": True,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    log_audit("SYSTEM_INIT", "Gran Tesoro VIP Gala loaded with full 4/4 capacity and 2 in Silver Room Queue.")

seed_sample_data()

# ==============================================================================
# HTML / CSS / JS FRONTEND TEMPLATE
# ==============================================================================
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gran Tesoro VIP Gala & Reverie Summit | RSVP Platform</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- FontAwesome & Google Fonts -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>

    <style>
        * { font-family: 'Plus Jakarta Sans', sans-serif; }
        .font-cinzel { font-family: 'Cinzel', serif; }
        
        /* Custom Gran Tesoro Gold Theme */
        :root {
            --gold: #f5c518;
            --gold-light: #ffeaa7;
            --gold-dark: #b8860b;
            --bg-dark: #07090e;
            --card-dark: #10141f;
            --border-gold: rgba(245, 197, 24, 0.25);
        }

        body {
            background-color: var(--bg-dark);
            color: #f1f2f6;
            background-image: radial-gradient(circle at 50% 0%, rgba(245, 197, 24, 0.08) 0%, transparent 50%),
                              radial-gradient(circle at 100% 100%, rgba(138, 43, 226, 0.05) 0%, transparent 40%);
            background-attachment: fixed;
        }

        .gold-gradient {
            background: linear-gradient(135deg, #ffd700 0%, #d4af37 50%, #aa7c11 100%);
        }

        .gold-border-glow {
            border: 1px solid var(--border-gold);
            box-shadow: 0 0 20px rgba(245, 197, 24, 0.1);
        }

        .glass-card {
            background: rgba(16, 20, 31, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.07);
        }

        /* Den Den Mushi Phone Vibration */
        @keyframes phoneRing {
            0% { transform: rotate(0) scale(1); }
            10% { transform: rotate(-15deg) scale(1.1); }
            20% { transform: rotate(15deg) scale(1.1); }
            30% { transform: rotate(-15deg) scale(1.1); }
            40% { transform: rotate(15deg) scale(1.1); }
            50% { transform: rotate(0) scale(1); }
            100% { transform: rotate(0) scale(1); }
        }
        .animate-ring { animation: phoneRing 1.2s infinite; }

        /* Holographic Gold Pass */
        .gold-pass {
            background: linear-gradient(135deg, #1e1b10 0%, #2d2612 50%, #15130b 100%);
            border: 2px solid #ffd700;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.25);
            position: relative;
            overflow: hidden;
        }
        .gold-pass::after {
            content: '';
            position: absolute;
            top: -50%; left: -50%; width: 200%; height: 200%;
            background: linear-gradient(60deg, transparent 40%, rgba(255, 255, 255, 0.15) 50%, transparent 60%);
            transform: rotate(30deg);
            animation: passShimmer 4s infinite;
        }
        @keyframes passShimmer {
            0% { transform: translateX(-100%) rotate(30deg); }
            100% { transform: translateX(100%) rotate(30deg); }
        }
    </style>
</head>
<body class="min-h-screen pb-16">

    <!-- TOP NAVIGATION & EVENT SELECTOR -->
    <header class="border-b border-white/10 bg-black/40 backdrop-blur-md sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 py-3.5 flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-11 h-11 rounded-xl gold-gradient flex items-center justify-center text-black font-black text-xl shadow-lg shadow-yellow-500/20">
                    <i class="fa-solid fa-crown"></i>
                </div>
                <div>
                    <h1 class="font-cinzel text-lg font-black tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-yellow-400 to-amber-500">
                        GRAN TESORO VIP RSVP
                    </h1>
                    <p class="text-xs text-gray-400">Smart Event Tech & Reverie Summit Access Control</p>
                </div>
            </div>

            <!-- Event Selector Tabs -->
            <div class="flex bg-white/5 p-1 rounded-xl border border-white/10 text-xs font-semibold gap-1" id="eventTabs">
                <button onclick="switchEvent('evt_tesoro')" class="px-3.5 py-2 rounded-lg transition-all event-tab bg-yellow-500 text-black font-bold shadow-md" id="tab_evt_tesoro">
                    🎰 Gran Tesoro Gala
                </button>
                <button onclick="switchEvent('evt_reverie')" class="px-3.5 py-2 rounded-lg transition-all event-tab text-gray-400 hover:text-white" id="tab_evt_reverie">
                    👑 Marijoa Reverie
                </button>
                <button onclick="switchEvent('evt_baratie')" class="px-3.5 py-2 rounded-lg transition-all event-tab text-gray-400 hover:text-white" id="tab_evt_baratie">
                    🍖 Baratie Chef's Table
                </button>
            </div>
        </div>
    </header>

    <!-- MAIN CONTAINER -->
    <main class="max-w-7xl mx-auto px-4 mt-8 space-y-8">

        <!-- INCOMING DEN DEN MUSHI SEAT OFFER BANNER (DYNAMIC MODAL) -->
        <div id="denDenMushiBanner" class="hidden">
            <div class="relative overflow-hidden bg-gradient-to-r from-emerald-950 via-gray-900 to-emerald-900 border-2 border-emerald-400/60 rounded-2xl p-6 shadow-2xl shadow-emerald-500/20">
                <div class="flex flex-col md:flex-row items-center justify-between gap-6 relative z-10">
                    <div class="flex items-center gap-5">
                        <div class="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-400 flex items-center justify-center text-3xl text-emerald-400 animate-ring">
                            <i class="fa-solid fa-phone-volume"></i>
                        </div>
                        <div>
                            <div class="flex items-center gap-2">
                                <span class="bg-emerald-500 text-black text-xs font-black px-2.5 py-0.5 rounded-full uppercase tracking-wider animate-pulse">
                                    Puru-Puru-Puru!
                                </span>
                                <span class="text-xs text-emerald-300 font-semibold" id="offerTimerText">Expires in 60s</span>
                            </div>
                            <h3 class="text-xl font-cinzel font-bold text-white mt-1" id="offerTitle">Golden Den Den Mushi Call for [Guest]</h3>
                            <p class="text-sm text-gray-300">A VIP Gold Room seat has opened up! You are #1 on the waitlist. Accept your invitation before it expires.</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-3 w-full md:w-auto">
                        <button onclick="declineSeatOffer()" class="flex-1 md:flex-none px-5 py-3 rounded-xl border border-red-500/40 text-red-400 hover:bg-red-500/10 font-bold text-sm transition">
                            Decline (Pass to Next)
                        </button>
                        <button onclick="acceptSeatOffer()" class="flex-1 md:flex-none px-7 py-3 rounded-xl bg-gradient-to-r from-emerald-400 to-teal-500 hover:from-emerald-300 hover:to-teal-400 text-black font-black text-sm shadow-lg shadow-emerald-500/30 transition transform hover:-translate-y-0.5">
                            <i class="fa-solid fa-check mr-1.5"></i> ACCEPT VIP SEAT
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- HERO EVENT DETAILS & METRICS -->
        <div class="glass-card rounded-2xl p-6 md:p-8 gold-border-glow relative overflow-hidden">
            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                <div>
                    <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/30 text-yellow-400 text-xs font-bold mb-3">
                        <i class="fa-solid fa-star"></i> OFFICIAL EVENT REGISTRATION
                    </div>
                    <h2 class="text-3xl md:text-4xl font-cinzel font-black text-white" id="heroEventName">Gran Tesoro VIP Golden Gala</h2>
                    <p class="text-gray-400 text-sm mt-1" id="heroTagline">Gild Tesoro's Exclusive 24K Casino Banquet</p>
                    <div class="flex flex-wrap items-center gap-4 text-xs text-gray-400 mt-4">
                        <span><i class="fa-solid fa-location-dot text-yellow-500 mr-1.5"></i> <span id="heroVenue">Gran Tesoro</span></span>
                        <span><i class="fa-regular fa-clock text-yellow-500 mr-1.5"></i> <span id="heroDate">Dec 31, 2025</span></span>
                        <span><i class="fa-solid fa-shield-halved text-yellow-500 mr-1.5"></i> <span id="heroOrganizer">Gild Tesoro</span></span>
                    </div>
                </div>

                <!-- Live Capacity Stats Gauge -->
                <div class="bg-black/50 border border-white/10 rounded-2xl p-5 min-w-[300px]">
                    <div class="flex justify-between items-center text-sm mb-2">
                        <span class="text-gray-400 font-semibold">VIP Room Occupancy</span>
                        <span class="font-black text-yellow-400 text-base" id="occupancyRatio">4 / 4 Seats</span>
                    </div>
                    <div class="w-full bg-gray-800 rounded-full h-3.5 overflow-hidden p-0.5 border border-white/5">
                        <div id="capacityProgressBar" class="h-full rounded-full gold-gradient transition-all duration-500" style="width: 100%;"></div>
                    </div>
                    <div class="flex justify-between items-center text-xs mt-3">
                        <span id="capacityStatusBadge" class="px-2.5 py-0.5 rounded-md bg-red-500/20 text-red-400 font-bold border border-red-500/30">
                            FULL CAPACITY
                        </span>
                        <span class="text-gray-400" id="waitlistCountBadge">Waitlist: 2 Queued</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 2-COLUMN MAIN INTERACTION GRID -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            <!-- LEFT COLUMN (5 Cols): Registration Form & Live Audit Terminal -->
            <div class="lg:col-span-5 space-y-8">

                <!-- RSVP / Registration Card -->
                <div class="glass-card rounded-2xl p-6 gold-border-glow">
                    <div class="flex items-center justify-between mb-5 pb-3 border-b border-white/10">
                        <h3 class="font-cinzel font-bold text-lg text-yellow-400 flex items-center gap-2">
                            <i class="fa-solid fa-ticket"></i> RSVP / Claim Seat Pass
                        </h3>
                        <span class="text-xs text-gray-400">Fair FIFO Queue</span>
                    </div>

                    <form id="rsvpForm" class="space-y-4">
                        <div>
                            <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">Guest Full Name</label>
                            <input type="text" id="regName" placeholder="e.g. Nico Robin" required
                                   class="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-yellow-500 transition">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">Den Den Mushi (Email)</label>
                            <input type="email" id="regEmail" placeholder="robin@strawhat.com" required
                                   class="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-yellow-500 transition">
                        </div>
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">Affiliation / Crew</label>
                                <select id="regAffiliation" class="w-full bg-black/60 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-yellow-500">
                                    <option value="Straw Hat Pirates">Straw Hat Pirates</option>
                                    <option value="World Government / Reverie">World Government Royal</option>
                                    <option value="Heart Pirates">Heart Pirates</option>
                                    <option value="Red Hair Pirates">Red Hair Pirates</option>
                                    <option value="Revolutionary Army">Revolutionary Army</option>
                                    <option value="Gran Tesoro VIP">High Roller Guest</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">Bounty (฿ Belly)</label>
                                <input type="text" id="regBounty" placeholder="e.g. 500,000,000 ฿" value="500,000,000 ฿"
                                       class="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-yellow-500">
                            </div>
                        </div>

                        <button type="submit" class="w-full py-3.5 rounded-xl gold-gradient font-black text-black text-sm tracking-wider uppercase hover:opacity-95 shadow-lg shadow-yellow-500/20 transition transform hover:-translate-y-0.5 mt-2">
                            Submit RSVP / Join Waitlist
                        </button>
                    </form>
                </div>

                <!-- Dynamic Organizer Controls (Capacity Modifier & Test Simulation) -->
                <div class="glass-card rounded-2xl p-6 border border-white/10">
                    <h3 class="font-cinzel font-bold text-sm text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <i class="fa-solid fa-sliders text-yellow-500"></i> Event Organizer Controls
                    </h3>
                    <div class="space-y-4">
                        <div>
                            <div class="flex justify-between text-xs font-semibold mb-1.5">
                                <span class="text-gray-400">Modify Room Capacity</span>
                                <span class="text-yellow-400 font-bold" id="capacityControlVal">4 Seats</span>
                            </div>
                            <div class="flex items-center gap-3">
                                <button onclick="changeCapacity(-1)" class="w-9 h-9 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 font-black text-base">-</button>
                                <input type="range" id="capacitySlider" min="1" max="10" value="4" oninput="updateCapacitySlider(this.value)" class="flex-1 accent-yellow-500">
                                <button onclick="changeCapacity(1)" class="w-9 h-9 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 font-black text-base">+</button>
                            </div>
                        </div>
                        <div class="pt-2 border-t border-white/5 flex gap-2">
                            <button onclick="triggerSimulatedCancellation()" class="flex-1 py-2 px-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-xs font-bold text-gray-300 transition">
                                🎲 Simulate Random Cancellation
                            </button>
                            <button onclick="resetData()" class="py-2 px-3 rounded-lg bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 text-xs font-bold text-red-400 transition">
                                <i class="fa-solid fa-rotate-left mr-1"></i> Reset
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Live Audit Stream Terminal -->
                <div class="glass-card rounded-2xl p-5 border border-white/10">
                    <div class="flex items-center justify-between mb-3 text-xs">
                        <span class="font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                            <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> Live System Audit Log
                        </span>
                        <span class="text-gray-500 font-mono text-[10px]" id="auditCount">0 events</span>
                    </div>
                    <div id="auditLogStream" class="h-44 overflow-y-auto space-y-2 pr-1 font-mono text-xs">
                        <!-- Dynamic logs -->
                    </div>
                </div>

            </div>

            <!-- RIGHT COLUMN (7 Cols): Gold Room Visualizer & Silver Room Waitlist -->
            <div class="lg:col-span-7 space-y-8">

                <!-- VIP GOLD ROOM SEAT MAP VISUALIZER -->
                <div class="glass-card rounded-2xl p-6 gold-border-glow">
                    <div class="flex items-center justify-between mb-5 pb-3 border-b border-white/10">
                        <div>
                            <h3 class="font-cinzel font-bold text-lg text-yellow-400 flex items-center gap-2">
                                <i class="fa-solid fa-champagne-glasses"></i> VIP Gold Room Floor Plan
                            </h3>
                            <p class="text-xs text-gray-400">Confirmed seat holders with entry credentials</p>
                        </div>
                        <span class="px-3 py-1 rounded-full bg-yellow-500/10 text-yellow-400 text-xs font-bold border border-yellow-500/30" id="confirmedBadge">
                            4 Confirmed
                        </span>
                    </div>

                    <!-- Seat Grid Container -->
                    <div id="seatGrid" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <!-- Dynamic Seat Cards -->
                    </div>
                </div>

                <!-- SILVER ROOM WAITLIST (FAIR FIFO QUEUE) -->
                <div class="glass-card rounded-2xl p-6 border border-white/10">
                    <div class="flex items-center justify-between mb-5 pb-3 border-b border-white/10">
                        <div>
                            <h3 class="font-cinzel font-bold text-lg text-gray-300 flex items-center gap-2">
                                <i class="fa-solid fa-hourglass-half text-gray-400"></i> Silver Room Queue (Waitlist)
                            </h3>
                            <p class="text-xs text-gray-400">Fair First-In, First-Out (FIFO) queue priority</p>
                        </div>
                        <span class="px-3 py-1 rounded-full bg-gray-500/20 text-gray-300 text-xs font-bold border border-gray-400/30" id="waitlistTotalBadge">
                            2 Queued
                        </span>
                    </div>

                    <div id="waitlistContainer" class="space-y-3">
                        <!-- Dynamic Waitlist entries -->
                    </div>
                </div>

            </div>

        </div>

    </main>

    <!-- COLLECTIBLE GOLDEN VIP ENTRY PASS MODAL -->
    <div id="vipPassModal" class="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4 hidden">
        <div class="max-w-md w-full gold-pass rounded-3xl p-8 relative transform transition-all scale-100">
            <button onclick="closePassModal()" class="absolute top-4 right-4 w-8 h-8 rounded-full bg-black/50 text-white hover:bg-black flex items-center justify-center text-sm z-20">
                <i class="fa-solid fa-xmark"></i>
            </button>
            
            <div class="text-center border-b border-yellow-500/30 pb-4 mb-4 relative z-10">
                <p class="text-[10px] font-black uppercase tracking-widest text-yellow-400">OFFICIAL WORLD GOVERNMENT ENTRY PASS</p>
                <h3 class="font-cinzel text-2xl font-black text-yellow-300 mt-1" id="passEventName">Gran Tesoro VIP Gala</h3>
                <p class="text-xs text-yellow-200/70 font-semibold" id="passTier">👑 Celestial Dragon VIP</p>
            </div>

            <div class="space-y-4 text-center my-6 relative z-10">
                <div class="w-20 h-20 rounded-full gold-gradient mx-auto flex items-center justify-center text-3xl text-black font-black border-4 border-yellow-300 shadow-xl">
                    <span id="passInitials">LU</span>
                </div>
                <div>
                    <h4 class="text-xl font-bold text-white font-cinzel" id="passGuestName">Monkey D. Luffy</h4>
                    <p class="text-xs text-yellow-400 font-mono" id="passAffiliation">Straw Hat Pirates</p>
                </div>
                <div class="grid grid-cols-2 gap-2 bg-black/40 p-3 rounded-xl border border-yellow-500/20 text-xs">
                    <div>
                        <span class="text-gray-400 block text-[10px]">SEAT NUMBER</span>
                        <span class="font-black text-yellow-300 text-sm" id="passSeatNum">Seat #1</span>
                    </div>
                    <div>
                        <span class="text-gray-400 block text-[10px]">REGISTERED AT</span>
                        <span class="font-semibold text-gray-200" id="passDate">Today</span>
                    </div>
                </div>
            </div>

            <div class="border-t border-yellow-500/30 pt-4 text-center relative z-10">
                <div class="inline-block p-2 bg-white rounded-lg mb-2">
                    <i class="fa-solid fa-qrcode text-black text-4xl"></i>
                </div>
                <p class="text-[10px] font-mono text-yellow-400/80">VALIDATED BY GILD TESORO ENTERTAINMENT BUREAU</p>
            </div>
        </div>
    </div>

    <!-- JAVASCRIPT STATE ENGINE -->
    <script>
        let currentEventId = "evt_tesoro";
        let activeOffer = null;
        let offerCountdownInterval = null;
        let offerRemainingSeconds = 60;

        // Audio synthesis for Den Den Mushi call using Web Audio API (Zero external audio dependency!)
        function playDenDenMushiRingtone() {
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                for (let i = 0; i < 3; i++) {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(800 + (i % 2 === 0 ? 150 : 0), ctx.currentTime + (i * 0.18));
                    gain.gain.setValueAtTime(0.15, ctx.currentTime + (i * 0.18));
                    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + (i * 0.18) + 0.15);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(ctx.currentTime + (i * 0.18));
                    osc.stop(ctx.currentTime + (i * 0.18) + 0.16);
                }
            } catch (e) { console.log('Audio autoplay prevented'); }
        }

        async function fetchDashboard() {
            const res = await fetch(`/api/dashboard?event_id=${currentEventId}`);
            const data = await res.json();
            renderDashboard(data);
        }

        function renderDashboard(data) {
            const evt = data.event;

            // Hero Details
            document.getElementById('heroEventName').innerText = evt.name;
            document.getElementById('heroTagline').innerText = evt.tagline;
            document.getElementById('heroVenue').innerText = evt.venue;
            document.getElementById('heroDate').innerText = evt.date;
            document.getElementById('heroOrganizer').innerText = evt.organizer;

            // Capacity Bar & Badges
            const confirmedCount = data.confirmed.length;
            const cap = evt.capacity;
            const pct = Math.min(100, Math.round((confirmedCount / cap) * 100));

            document.getElementById('occupancyRatio').innerText = `${confirmedCount} / ${cap} Seats`;
            document.getElementById('capacityProgressBar').style.width = `${pct}%`;
            document.getElementById('capacitySlider').value = cap;
            document.getElementById('capacityControlVal').innerText = `${cap} Seats`;

            const statusBadge = document.getElementById('capacityStatusBadge');
            if (confirmedCount >= cap) {
                statusBadge.innerText = 'FULL CAPACITY (WAITLIST ACTIVE)';
                statusBadge.className = 'px-2.5 py-0.5 rounded-md bg-red-500/20 text-red-400 font-bold border border-red-500/30';
            } else {
                statusBadge.innerText = `${cap - confirmedCount} SEATS AVAILABLE`;
                statusBadge.className = 'px-2.5 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30';
            }

            document.getElementById('waitlistCountBadge').innerText = `Waitlist: ${data.waitlist.length} Queued`;
            document.getElementById('confirmedBadge').innerText = `${confirmedCount} Confirmed`;
            document.getElementById('waitlistTotalBadge').innerText = `${data.waitlist.length} Queued`;

            // Render Confirmed Seats
            const seatGrid = document.getElementById('seatGrid');
            if (data.confirmed.length === 0) {
                seatGrid.innerHTML = `<div class="col-span-2 text-center py-8 text-gray-500 text-sm">No guests in VIP Gold Room yet.</div>`;
            } else {
                seatGrid.innerHTML = data.confirmed.map(g => `
                    <div class="bg-black/40 border border-yellow-500/20 hover:border-yellow-500/50 p-4 rounded-xl transition flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-[11px] font-mono font-bold text-yellow-400 bg-yellow-500/10 px-2 py-0.5 rounded border border-yellow-500/30">
                                    SEAT #${g.seat_number}
                                </span>
                                <span class="text-[10px] text-gray-400">${g.bounty}</span>
                            </div>
                            <h4 class="font-bold text-white text-base">${g.name}</h4>
                            <p class="text-xs text-yellow-300/80 font-semibold">${g.vip_tier}</p>
                            <p class="text-xs text-gray-400 mt-0.5">${g.affiliation}</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-white/5 flex gap-2">
                            <button onclick="viewGoldPass('${g.name}', '${g.vip_tier}', '${g.affiliation}', '${g.seat_number}', '${g.registered_at}')"
                                    class="flex-1 py-1.5 rounded-lg bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500 hover:text-black font-bold text-xs transition">
                                <i class="fa-solid fa-id-card mr-1"></i> Pass
                            </button>
                            <button onclick="cancelRegistration('${g.id}', '${g.name}')"
                                    class="py-1.5 px-3 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500 hover:text-white font-bold text-xs transition">
                                Cancel Seat
                            </button>
                        </div>
                    </div>
                `).join('');
            }

            // Render Waitlist
            const wlContainer = document.getElementById('waitlistContainer');
            if (data.waitlist.length === 0) {
                wlContainer.innerHTML = `<div class="text-center py-6 text-gray-500 text-sm">Silver Room Queue is empty. No one waiting.</div>`;
            } else {
                wlContainer.innerHTML = data.waitlist.map(w => `
                    <div class="bg-black/40 border border-white/10 p-3.5 rounded-xl flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full bg-gray-800 border border-gray-600 flex items-center justify-center font-bold text-xs text-yellow-400">
                                #${w.position}
                            </div>
                            <div>
                                <h5 class="font-bold text-sm text-white">${w.name} <span class="text-xs text-gray-400 font-normal">(${w.affiliation})</span></h5>
                                <p class="text-[11px] text-gray-400">${w.rank_title} • Bounty: ${w.bounty}</p>
                            </div>
                        </div>
                        <span class="text-xs font-semibold px-2.5 py-1 rounded-md bg-white/5 text-gray-300 border border-white/10">
                            FIFO Queued
                        </span>
                    </div>
                `).join('');
            }

            // Active Den Den Mushi Offer handling
            if (data.active_offer && data.active_offer.status === "PENDING") {
                activeOffer = data.active_offer;
                document.getElementById('denDenMushiBanner').classList.remove('hidden');
                document.getElementById('offerTitle').innerText = `Golden Den Den Mushi Invitation for ${activeOffer.name}`;
                startOfferCountdown();
            } else {
                document.getElementById('denDenMushiBanner').classList.add('hidden');
                clearInterval(offerCountdownInterval);
            }

            // Audit Logs
            document.getElementById('auditCount').innerText = `${data.audit_logs.length} logged`;
            document.getElementById('auditLogStream').innerHTML = data.audit_logs.map(log => `
                <div class="text-[11px] text-gray-400 border-b border-white/5 pb-1">
                    <span class="text-yellow-500 font-bold">[${log.time}]</span> 
                    <span class="text-gray-300 font-semibold">${log.action}</span>: ${log.details}
                </div>
            `).join('');
        }

        // Countdown Timer for Den Den Mushi Offer
        function startOfferCountdown() {
            clearInterval(offerCountdownInterval);
            offerRemainingSeconds = 60;
            playDenDenMushiRingtone();

            offerCountdownInterval = setInterval(() => {
                offerRemainingSeconds--;
                document.getElementById('offerTimerText').innerText = `Expires in ${offerRemainingSeconds}s`;
                if (offerRemainingSeconds <= 0) {
                    clearInterval(offerCountdownInterval);
                    declineSeatOffer(true); // Auto-expire
                }
            }, 1000);
        }

        // Form Submit
        document.getElementById('rsvpForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('regName').value;
            const email = document.getElementById('regEmail').value;
            const affiliation = document.getElementById('regAffiliation').value;
            const bounty = document.getElementById('regBounty').value;

            const res = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event_id: currentEventId, name, email, affiliation, bounty })
            });
            const data = await res.json();
            
            if (data.type === "CONFIRMED") {
                confetti({ particleCount: 80, spread: 60, origin: { y: 0.6 } });
            }
            alert(data.message);
            document.getElementById('regName').value = '';
            document.getElementById('regEmail').value = '';
            fetchDashboard();
        });

        // Cancel Seat
        async function cancelRegistration(regId, guestName) {
            if (!confirm(`Revoke / Cancel VIP seat for ${guestName}? A Golden Den Den Mushi call will immediately summon the next waitlisted guest.`)) return;
            const res = await fetch('/api/cancel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event_id: currentEventId, reg_id: regId })
            });
            const data = await res.json();
            fetchDashboard();
        }

        // Accept Offer
        async function acceptSeatOffer() {
            if (!activeOffer) return;
            const res = await fetch('/api/accept-offer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ offer_id: activeOffer.id })
            });
            const data = await res.json();
            confetti({ particleCount: 120, spread: 80, origin: { y: 0.5 } });
            alert(data.message);
            fetchDashboard();
        }

        // Decline Offer
        async function declineSeatOffer(isExpired = false) {
            if (!activeOffer) return;
            const res = await fetch('/api/decline-offer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ offer_id: activeOffer.id, expired: isExpired })
            });
            const data = await res.json();
            fetchDashboard();
        }

        // Capacity Slider
        async function updateCapacitySlider(val) {
            document.getElementById('capacityControlVal').innerText = `${val} Seats`;
            await fetch('/api/update-capacity', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event_id: currentEventId, capacity: parseInt(val) })
            });
            fetchDashboard();
        }

        function changeCapacity(delta) {
            const slider = document.getElementById('capacitySlider');
            const newVal = Math.max(1, Math.min(10, parseInt(slider.value) + delta));
            updateCapacitySlider(newVal);
        }

        // Simulate random cancellation
        async function triggerSimulatedCancellation() {
            await fetch('/api/simulate-cancellation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event_id: currentEventId })
            });
            fetchDashboard();
        }

        // Reset
        async function resetData() {
            if (!confirm('Reset all registrations to initial demo state?')) return;
            await fetch('/api/reset', { method: 'POST' });
            fetchDashboard();
        }

        // Event Switcher
        function switchEvent(evtId) {
            currentEventId = evtId;
            document.querySelectorAll('.event-tab').forEach(b => {
                b.className = 'px-3.5 py-2 rounded-lg transition-all event-tab text-gray-400 hover:text-white';
            });
            const activeTab = document.getElementById(`tab_${evtId}`);
            activeTab.className = 'px-3.5 py-2 rounded-lg transition-all event-tab bg-yellow-500 text-black font-bold shadow-md';
            fetchDashboard();
        }

        // VIP Pass Modal
        function viewGoldPass(name, tier, affil, seat, date) {
            document.getElementById('passEventName').innerText = document.getElementById('heroEventName').innerText;
            document.getElementById('passTier').innerText = tier;
            document.getElementById('passGuestName').innerText = name;
            document.getElementById('passAffiliation').innerText = affil;
            document.getElementById('passSeatNum').innerText = `Seat #${seat}`;
            document.getElementById('passDate').innerText = date;
            document.getElementById('passInitials').innerText = name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
            document.getElementById('vipPassModal').classList.remove('hidden');
        }

        function closePassModal() {
            document.getElementById('vipPassModal').classList.add('hidden');
        }

        // Live Poll
        fetchDashboard();
        setInterval(fetchDashboard, 2500);
    </script>
</body>
</html>
"""

# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================
@app.route("/")
def index():
    return render_template_string(FRONTEND_HTML)

@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    event_id = request.args.get("event_id", ACTIVE_EVENT_ID)
    evt = EVENTS.get(event_id, EVENTS["evt_tesoro"])

    confirmed = [r for r in REGISTRATIONS.values() if r["event_id"] == event_id and r["status"] == "CONFIRMED"]
    confirmed.sort(key=lambda x: x["seat_number"])

    active_wl = [w for w in WAITLIST.values() if w["event_id"] == event_id and w["is_active"]]
    active_wl.sort(key=lambda x: x["position"])

    pending_offer = next((o for o in OFFERS.values() if o["event_id"] == event_id and o["status"] == "PENDING"), None)

    return jsonify({
        "event": evt,
        "confirmed": confirmed,
        "waitlist": active_wl,
        "active_offer": pending_offer,
        "audit_logs": AUDIT_LOGS[:20]
    })

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    event_id = data.get("event_id", "evt_tesoro")
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    affiliation = data.get("affiliation", "Independent")
    bounty = data.get("bounty", "100,000,000 ฿")

    evt = EVENTS.get(event_id)
    if not evt:
        return jsonify({"success": False, "message": "Event not found"}), 404

    # Check existing
    if any(r["event_id"] == event_id and r["email"] == email and r["status"] == "CONFIRMED" for r in REGISTRATIONS.values()):
        return jsonify({"success": False, "message": "Guest is already confirmed in the VIP Gold Room!"}), 400

    if any(w["event_id"] == event_id and w["email"] == email and w["is_active"] for w in WAITLIST.values()):
        return jsonify({"success": False, "message": "Guest is already on the Silver Room waitlist!"}), 400

    confirmed = [r for r in REGISTRATIONS.values() if r["event_id"] == event_id and r["status"] == "CONFIRMED"]

    if len(confirmed) < evt["capacity"]:
        seat_num = len(confirmed) + 1
        tier = get_vip_tier(seat_num, evt["capacity"])
        rid = gen_id("REG")
        REGISTRATIONS[rid] = {
            "id": rid,
            "event_id": event_id,
            "name": name,
            "email": email,
            "affiliation": affiliation,
            "bounty": bounty,
            "seat_number": seat_num,
            "vip_tier": tier,
            "status": "CONFIRMED",
            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        log_audit("VIP_REGISTRATION", f"{name} claimed VIP Gold Room Seat #{seat_num} ({tier}).")
        return jsonify({"success": True, "type": "CONFIRMED", "message": f"🌟 VIP Entry Pass Issued for {name}! (Seat #{seat_num})"})
    else:
        # Waitlist
        current_wl = [w for w in WAITLIST.values() if w["event_id"] == event_id and w["is_active"]]
        pos = len(current_wl) + 1
        rank = get_rank_title(pos)
        wid = gen_id("WL")
        WAITLIST[wid] = {
            "id": wid,
            "event_id": event_id,
            "name": name,
            "email": email,
            "affiliation": affiliation,
            "bounty": bounty,
            "position": pos,
            "rank_title": rank,
            "is_active": True,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        log_audit("WAITLISTED", f"Capacity full. {name} placed in Silver Room Queue Position #{pos} ({rank}).")
        return jsonify({"success": True, "type": "WAITLISTED", "message": f"🥈 Gold Room full! {name} placed on Waitlist Position #{pos}."})

@app.route("/api/cancel", methods=["POST"])
def cancel():
    data = request.get_json() or {}
    event_id = data.get("event_id")
    reg_id = data.get("reg_id")

    reg = REGISTRATIONS.get(reg_id)
    if not reg or reg["status"] != "CONFIRMED":
        return jsonify({"success": False, "message": "Active registration not found"}), 404

    reg["status"] = "CANCELLED"
    log_audit("CANCELLATION", f"{reg['name']} cancelled their VIP Gold Room seat.")

    # Trigger Den Den Mushi Offer to next in line
    active_wl = [w for w in WAITLIST.values() if w["event_id"] == event_id and w["is_active"]]
    active_wl.sort(key=lambda x: x["position"])

    if active_wl:
        next_in_line = active_wl[0]
        oid = gen_id("OFR")
        OFFERS[oid] = {
            "id": oid,
            "event_id": event_id,
            "waitlist_id": next_in_line["id"],
            "name": next_in_line["name"],
            "email": next_in_line["email"],
            "affiliation": next_in_line["affiliation"],
            "bounty": next_in_line["bounty"],
            "status": "PENDING",
            "created_at": datetime.now().strftime("%H:%M:%S")
        }
        log_audit("OFFER_DISPATCHED", f"📞 Golden Den Den Mushi ringing for {next_in_line['name']} (Waitlist #1)!")
        return jsonify({"success": True, "message": f"Seat freed. Den Den Mushi invitation sent to {next_in_line['name']}!"})

    return jsonify({"success": True, "message": "Seat cancelled. No one on waitlist."})

@app.route("/api/accept-offer", methods=["POST"])
def accept_offer():
    data = request.get_json() or {}
    offer_id = data.get("offer_id")
    offer = OFFERS.get(offer_id)

    if not offer or offer["status"] != "PENDING":
        return jsonify({"success": False, "message": "Offer is invalid or expired"}), 400

    offer["status"] = "ACCEPTED"
    
    # Deactivate from waitlist
    wl_entry = WAITLIST.get(offer["waitlist_id"])
    if wl_entry:
        wl_entry["is_active"] = False

    # Renumber waitlist
    remaining_wl = [w for w in WAITLIST.values() if w["event_id"] == offer["event_id"] and w["is_active"]]
    remaining_wl.sort(key=lambda x: x["position"])
    for idx, w in enumerate(remaining_wl, start=1):
        w["position"] = idx
        w["rank_title"] = get_rank_title(idx)

    # Create confirmed registration
    evt = EVENTS.get(offer["event_id"])
    confirmed = [r for r in REGISTRATIONS.values() if r["event_id"] == offer["event_id"] and r["status"] == "CONFIRMED"]
    seat_num = len(confirmed) + 1
    tier = get_vip_tier(seat_num, evt["capacity"] if evt else 5)

    rid = gen_id("REG")
    REGISTRATIONS[rid] = {
        "id": rid,
        "event_id": offer["event_id"],
        "name": offer["name"],
        "email": offer["email"],
        "affiliation": offer["affiliation"],
        "bounty": offer["bounty"],
        "seat_number": seat_num,
        "vip_tier": tier,
        "status": "CONFIRMED",
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    log_audit("OFFER_ACCEPTED", f"🎉 {offer['name']} accepted Golden Den Den Mushi offer! Seat #{seat_num} claimed.")
    return jsonify({"success": True, "message": f"🎉 Seat confirmed! Welcome to the VIP Gold Room, {offer['name']}!"})

@app.route("/api/decline-offer", methods=["POST"])
def decline_offer():
    data = request.get_json() or {}
    offer_id = data.get("offer_id")
    offer = OFFERS.get(offer_id)

    if not offer or offer["status"] != "PENDING":
        return jsonify({"success": False, "message": "Offer not found"}), 400

    offer["status"] = "DECLINED"
    wl_entry = WAITLIST.get(offer["waitlist_id"])
    if wl_entry:
        wl_entry["is_active"] = False

    log_audit("OFFER_DECLINED", f"Offer declined/expired for {offer['name']}.")

    # Cascade to next person in line
    remaining_wl = [w for w in WAITLIST.values() if w["event_id"] == offer["event_id"] and w["is_active"]]
    remaining_wl.sort(key=lambda x: x["position"])
    for idx, w in enumerate(remaining_wl, start=1):
        w["position"] = idx
        w["rank_title"] = get_rank_title(idx)

    if remaining_wl:
        next_w = remaining_wl[0]
        oid = gen_id("OFR")
        OFFERS[oid] = {
            "id": oid,
            "event_id": offer["event_id"],
            "waitlist_id": next_w["id"],
            "name": next_w["name"],
            "email": next_w["email"],
            "affiliation": next_w["affiliation"],
            "bounty": next_w["bounty"],
            "status": "PENDING",
            "created_at": datetime.now().strftime("%H:%M:%S")
        }
        log_audit("OFFER_CASCADED", f"📞 Passed to next: Den Den Mushi ringing for {next_w['name']}!")

    return jsonify({"success": True, "message": "Offer passed to next in line."})

@app.route("/api/update-capacity", methods=["POST"])
def update_capacity():
    data = request.get_json() or {}
    event_id = data.get("event_id")
    new_cap = int(data.get("capacity", 4))
    if event_id in EVENTS:
        EVENTS[event_id]["capacity"] = new_cap
        log_audit("CAPACITY_UPDATED", f"Capacity for {EVENTS[event_id]['name']} changed to {new_cap} seats.")
    return jsonify({"success": True})

@app.route("/api/simulate-cancellation", methods=["POST"])
def simulate():
    data = request.get_json() or {}
    event_id = data.get("event_id", "evt_tesoro")
    confirmed = [r for r in REGISTRATIONS.values() if r["event_id"] == event_id and r["status"] == "CONFIRMED"]
    if confirmed:
        victim = confirmed[-1]
        victim["status"] = "CANCELLED"
        log_audit("SIMULATED_CANCEL", f"{victim['name']} left the banquet. Seat freed.")
        
        # Trigger offer
        active_wl = [w for w in WAITLIST.values() if w["event_id"] == event_id and w["is_active"]]
        active_wl.sort(key=lambda x: x["position"])
        if active_wl:
            next_w = active_wl[0]
            oid = gen_id("OFR")
            OFFERS[oid] = {
                "id": oid,
                "event_id": event_id,
                "waitlist_id": next_w["id"],
                "name": next_w["name"],
                "email": next_w["email"],
                "affiliation": next_w["affiliation"],
                "bounty": next_w["bounty"],
                "status": "PENDING",
                "created_at": datetime.now().strftime("%H:%M:%S")
            }
    return jsonify({"success": True})

@app.route("/api/reset", methods=["POST"])
def reset():
    seed_sample_data()
    return jsonify({"success": True})

# ==============================================================================
# AUTO LAUNCH BROWSER
# ==============================================================================
def open_browser():
    time.sleep(1.0)
    print("\n🌐 Launching Gran Tesoro VIP Web App in browser...")
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    print("🏆 Starting Gran Tesoro VIP RSVP Web Platform at http://127.0.0.1:5000 ...")
    app.run(port=5000, debug=False)