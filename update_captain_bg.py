"""
Gran Tesoro - Captain's Desk Background Updater
Embeds your One Piece photo specifically into the Captain's Desk modal/panel.
"""
import os
import base64

static_dir = "static"
html_path = os.path.join(static_dir, "index.html")

if not os.path.exists(html_path):
    print("❌ Error: static/index.html not found!")
    exit()

# Find captain background photo in static/
def get_captain_bg():
    files = os.listdir(static_dir)
    print("📁 Files in static/:", files)
    
    # Look for captain, desk, or bg images
    for filename in files:
        f_lower = filename.lower()
        if f_lower != "index.html" and any(k in f_lower for k in ["captain", "desk", "organizer"]):
            filepath = os.path.join(static_dir, filename)
            ext = filename.split('.')[-1].lower()
            if ext == 'jpg': ext = 'jpeg'
            mime = f"image/{ext}" if ext in ['jpeg', 'png', 'webp'] else "image/jpeg"
            with open(filepath, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                print(f"📸 Found Captain's Desk photo: {filename}")
                return f"data:{mime};base64,{encoded}"
                
    # Fallback to any captain_bg file
    for filename in files:
        if filename.lower().startswith("captain_bg"):
            filepath = os.path.join(static_dir, filename)
            ext = filename.split('.')[-1].lower()
            if ext == 'jpg': ext = 'jpeg'
            mime = f"image/{ext}"
            with open(filepath, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                print(f"📸 Found Captain's Desk photo: {filename}")
                return f"data:{mime};base64,{encoded}"
                
    return None

captain_bg_b64 = get_captain_bg()

if not captain_bg_b64:
    print("\n❌ Error: Could not find captain_bg.jpg inside static/ folder!")
    print("Please save your One Piece photo in static/ named 'captain_bg.jpg' or 'captain_bg.png'!")
    exit()

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# CSS Rule specifically targeting Captain's Desk with dark overlay for readable text
captain_desk_css = f"""
/* CAPTAIN'S DESK ONE PIECE BACKGROUND */
#captainDesk,
.captain-desk,
.captain-desk-modal,
.captain-desk-panel,
#deskModal,
#vCaptain,
.desk-modal,
.desk-content {{
  background: linear-gradient(rgba(12, 6, 9, 0.78), rgba(12, 6, 9, 0.88)), url("{captain_bg_b64}") center/cover no-repeat !important;
  border: 2px solid #e0b34a !important;
  box-shadow: 0 20px 50px rgba(0,0,0,0.85), inset 0 0 20px rgba(224,179,74,0.15) !important;
}}
"""

if "/* CAPTAIN'S DESK ONE PIECE BACKGROUND */" in html:
    # Update existing
    import re
    html = re.sub(
        r'/\* CAPTAIN\'S DESK ONE PIECE BACKGROUND \*/[\s\S]*?\}',
        captain_desk_css.strip(),
        html
    )
    print("✅ Updated existing Captain's Desk background CSS!")
else:
    # Inject before </style>
    html = html.replace("</style>", f"{captain_desk_css}\n</style>", 1)
    print("✅ Injected Captain's Desk background CSS!")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("\n🎉 SUCCESS! Captain's Desk background updated with your One Piece photo!")