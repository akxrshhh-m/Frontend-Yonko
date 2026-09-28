"""
One Piece Theme Integration - Gran Tesoro & Reverie
"""

# ASCII Art Banner
BANNER = r"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     ██████╗ ██████╗  █████╗ ███╗   ██╗    ████████╗███████╗███████╗  ║
║    ██╔════╝ ██╔══██╗██╔══██╗████╗  ██║    ╚══██╔══╝██╔════╝██╔════╝  ║
║    ██║  ███╗██████╔╝███████║██╔██╗ ██║       ██║   █████╗  ███████╗  ║
║    ██║   ██║██╔══██╗██╔══██║██║╚██╗██║       ██║   ██╔══╝  ╚════██║  ║
║    ╚██████╔╝██║  ██║██║  ██║██║ ╚████║       ██║   ███████╗███████║  ║
║     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝       ╚═╝   ╚══════╝╚══════╝  ║
║                                                                      ║
║          🏆 VIP GALA & WORLD GOVERNMENT REVERIE SUMMIT 🏆           ║
║                  Smart Event RSVP Management System                  ║
║                                                                      ║
║    "Step into the golden city where only the chosen may enter..."    ║
║                        — Gild Tesoro                                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""

# Theme flavor text for various operations
FLAVOR_TEXT = {
    "event_created": "🎰 A new spectacle has been announced at Gran Tesoro!",
    "registration_success": "🌟 Welcome to the VIP Gold Room! Your entry pass has been issued.",
    "registration_waitlisted": "🥈 The Gold Room is full. You've been placed in the Silver Room Queue.",
    "cancellation": "🚪 A guest has departed Gran Tesoro. A seat opens in the Gold Room...",
    "offer_sent": "📞 A Golden Den Den Mushi call has been placed! An invitation awaits...",
    "offer_accepted": "🎉 The invitation has been accepted! Welcome to the Gold Room, VIP!",
    "offer_declined": "❌ The invitation was declined. The next in queue shall be summoned.",
    "offer_expired": "⏰ The Golden Den Den Mushi rang unanswered. The offer has expired.",
    "event_full": "🔒 Gran Tesoro's Gold Room has reached maximum capacity!",
    "event_closed": "🚫 The gates of Gran Tesoro have closed for this event.",
    "waitlist_empty": "📋 The Silver Room Queue is empty. No one awaits entry.",
    "capacity_updated": "🏗️ Gran Tesoro's Gold Room capacity has been adjusted!",
}

# Themed event templates
EVENT_TEMPLATES = {
    "gran_tesoro_gala": {
        "name": "Gran Tesoro VIP Golden Gala",
        "description": "An exclusive evening of entertainment at Gild Tesoro's legendary golden casino ship. "
                       "Featuring performances, gourmet dining, and the grandest spectacle on the seas!",
        "venue": "Gran Tesoro - Entertainment City (Ship)",
        "default_capacity": 100,
    },
    "reverie_summit": {
        "name": "World Government Reverie Summit",
        "description": "The sacred council at Marijoa where rulers of 50 allied kingdoms gather "
                       "to discuss the fate of the world. By invitation of the Five Elders only.",
        "venue": "Sacred Marijoa - Pangaea Castle",
        "default_capacity": 50,
    },
    "davy_back_fight": {
        "name": "Davy Back Fight Championship",
        "description": "The legendary pirate competition! Crews compete in a series of challenges "
                       "with crew members as the ultimate stakes!",
        "venue": "Long Ring Long Land",
        "default_capacity": 200,
    },
    "baratie_dinner": {
        "name": "Baratie Exclusive Chef's Table",
        "description": "An intimate dining experience at the floating restaurant Baratie, "
                       "prepared by the legendary chefs of the All Blue dream.",
        "venue": "Baratie - Floating Restaurant, East Blue",
        "default_capacity": 20,
    },
}


def get_rank_title(position: int) -> str:
    """Get a One Piece themed rank based on waitlist position."""
    if position == 1:
        return "Yonko-Level Priority"
    elif position <= 3:
        return "Warlord-Level Priority"
    elif position <= 10:
        return "Supernova-Level Priority"
    elif position <= 25:
        return "Grand Line Pirate Priority"
    else:
        return "East Blue Rookie Priority"


def get_vip_tier(registration_number: int, total_capacity: int) -> str:
    """Get VIP tier based on registration order."""
    ratio = registration_number / total_capacity if total_capacity > 0 else 1
    if ratio <= 0.1:
        return "Celestial Dragon Tier (Ultra VIP)"
    elif ratio <= 0.25:
        return "Admiral Tier (Premium VIP)"
    elif ratio <= 0.5:
        return "Captain Tier (Standard VIP)"
    else:
        return "Crew Member Tier (General)"