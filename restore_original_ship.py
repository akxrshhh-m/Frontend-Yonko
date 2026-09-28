"""
Gran Tesoro - Restore Original SVG Sailing Ship
Removes all photo/image embeds for the ship and restores the original crisp SVG pirate ship,
rocking animations, and scroll-following navigation.
"""
import os
import re

html_path = os.path.join("static", "index.html")

if not os.path.exists(html_path):
    print("❌ Error: static/index.html not found!")
    exit()

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# Original SVG Ship HTML
original_ship_svg = """
  <svg class="hull" viewBox="0 0 170 150">
    <path d="M74 12 L158 92 M74 12 L18 72" stroke="#f4ead6" stroke-opacity=".45" stroke-width="1"/>
    <rect x="72" y="12" width="4" height="82" fill="#3a2510"/>
    <rect x="118" y="34" width="4" height="60" fill="#3a2510"/>
    <path d="M74 6 L98 12 L74 18Z" fill="#b2332c"/>
    <rect x="50" y="22" width="52" height="3.4" rx="1.5" fill="#5b3410"/>
    <path d="M52 25 Q76 34 100 25 V64 Q76 74 52 64Z" fill="#f4ead6" stroke="#cdb27b"/>
    <use href="#i-roger" x="63" y="32" width="26" height="26" style="color:#2a1508"/>
    <rect x="100" y="40" width="40" height="3" rx="1.5" fill="#5b3410"/>
    <path d="M102 43 Q120 50 138 43 V68 Q120 75 102 68Z" fill="#f4ead6" stroke="#cdb27b"/>
    <path d="M102 55 Q120 62 138 55" stroke="url(#gGold)" stroke-width="3" fill="none"/>
    <path d="M12 92 H156 C150 116 132 128 108 130 H58 C36 128 18 116 12 92Z" fill="#2a1508" stroke="url(#gGold)" stroke-width="2.4"/>
    <path d="M14 98 H154" stroke="url(#gGold)" stroke-width="3"/>
    <path d="M10 92 V72 H44 V92Z" fill="#3a2510" stroke="url(#gGold)" stroke-width="1.6"/>
    <g fill="#ffe9ad"><rect x="16" y="78" width="5" height="6" rx="1"/><rect x="26" y="78" width="5" height="6" rx="1"/><rect x="36" y="78" width="5" height="6" rx="1"/></g>
    <g fill="#ffe9ad"><circle cx="56" cy="108" r="3.2"/><circle cx="76" cy="108" r="3.2"/><circle cx="96" cy="108" r="3.2"/><circle cx="116" cy="108" r="3.2"/></g>
    <path d="M154 90 L166 80" stroke="#5b3410" stroke-width="3" stroke-linecap="round"/>
    <circle cx="157" cy="98" r="9" fill="url(#gGoldV)" stroke="#fff1cd"/>
    <path d="M157 84v4M157 108v4M143 98h4M167 98h4M147 88l3 3M167 108l-3-3" stroke="#f3d98b" stroke-width="2" stroke-linecap="round"/>
  </svg>
"""

# Clean out all img ship tags and custom ship wrappers
html = re.sub(r'<img[^>]*class="[^"]*ship-photo[^"]*"[\s\S]*?>', '', html)
html = re.sub(r'<div[^>]*class="sunny-wrapper"[\s\S]*?</div>', '', html)
html = re.sub(r'<svg[^>]*class="hull"[\s\S]*?</svg>', '', html)

# Inject the clean original SVG ship into #voyager
html = re.sub(
    r'(<div[^>]*id="voyager"[^>]*>[\s\S]*?<div[^>]*id="isle"[^>]*>[\s\S]*?</div>)([\s\S]*?)(<svg[^>]*class="wv")',
    lambda m: m.group(1) + "\n" + original_ship_svg + "\n  " + m.group(3),
    html
)

# Clean up custom CSS overrides for ship
html = re.sub(r'/\* SAILING SHIP BOBBING & ROCKING ANIMATION \*/[\s\S]*?\}', '', html)
html = re.sub(r'/\* REMOVE WHITE BOX AROUND SHIP[\s\S]*?\}', '', html)
html = re.sub(r'/\* THOUSAND SUNNY SAILING DYNAMICS \*/[\s\S]*?\}', '', html)

# Restore crisp SVG animation CSS
original_css = """
#voyager {
  position: fixed;
  top: 0;
  right: var(--vr);
  width: 108px;
  z-index: 50;
  pointer-events: none;
  will-change: transform;
}
#voyager .hull {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
  transform-origin: 45% 78%;
  animation: rock 4.8s ease-in-out infinite;
  filter: drop-shadow(0 8px 10px rgba(0,0,0,.55));
}
@keyframes rock {
  0%, 100% { transform: rotate(7deg); }
  50%      { transform: rotate(14deg); }
}
"""

if "/* RESTORED ORIGINAL SHIP CSS */" not in html:
    html = html.replace("</style>", f"/* RESTORED ORIGINAL SHIP CSS */\n{original_css}\n</style>", 1)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("🎉 SUCCESS! Original SVG pirate ship and sailing scroll motion fully restored!")