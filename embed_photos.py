"""
Gran Tesoro - Guaranteed Base64 Photo Embedder
Reads your photos from static/ and embeds them directly into index.html.
No file paths, no 404s, no caching issues!
"""
import os
import base64
import re

static_dir = "static"
html_path = os.path.join(static_dir, "index.html")

if not os.path.exists(html_path):
    print("❌ Error: static/index.html not found!")
    exit()

def get_base64_data(keyword):
    if not os.path.exists(static_dir):
        return None
    for filename in os.listdir(static_dir):
        if keyword in filename.lower() and filename.lower() != "index.html":
            filepath = os.path.join(static_dir, filename)
            ext = filename.split('.')[-1].lower()
            if ext == 'jpg': ext = 'jpeg'
            mime = f"image/{ext}" if ext in ['jpeg', 'png', 'webp', 'gif'] else "image/jpeg"
            with open(filepath, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                print(f"📸 Found photo for {keyword.upper()}: {filename} ({len(encoded)} bytes)")
                return f"data:{mime};base64,{encoded}"
    return None

zoro_b64 = get_base64_data("zoro")
nami_b64 = get_base64_data("nami")
luffy_b64 = get_base64_data("luffy")

if not (zoro_b64 or nami_b64 or luffy_b64):
    print("❌ Error: Could not find any luffy, zoro, or nami photo files inside static/ folder!")
    exit()

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

def make_img(b64_str, alt):
    return f'<div class="fr" style="padding:0; overflow:hidden; border:2px solid #3a2a12; height:92px; display:block;"><img src="{b64_str}" alt="{alt}" style="width:100%; height:100%; object-fit:cover; display:block;"></div>'

# Embed Zoro (Poster A)
if zoro_b64:
    html = re.sub(
        r'(<div[^>]*class="wp a"[^>]*>[\s\S]*?)(<div[^>]*class="fr"[^>]*>[\s\S]*?</div>)([\s\S]*?<span[^>]*class="n">)',
        lambda m: m.group(1) + make_img(zoro_b64, "Zoro") + m.group(3),
        html
    )

# Embed Nami (Poster B)
if nami_b64:
    html = re.sub(
        r'(<div[^>]*class="wp b"[^>]*>[\s\S]*?)(<div[^>]*class="fr"[^>]*>[\s\S]*?</div>)([\s\S]*?<span[^>]*class="n">)',
        lambda m: m.group(1) + make_img(nami_b64, "Nami") + m.group(3),
        html
    )

# Embed Luffy (Poster C)
if luffy_b64:
    html = re.sub(
        r'(<div[^>]*class="wp c"[^>]*>[\s\S]*?)(<div[^>]*class="fr"[^>]*>[\s\S]*?</div>)([\s\S]*?<span[^>]*class="n">)',
        lambda m: m.group(1) + make_img(luffy_b64, "Luffy") + m.group(3),
        html
    )

# Embed default modal poster image
if luffy_b64:
    html = re.sub(
        r'id="poImg"\s+src="[^"]*"',
        f'id="poImg" src="{luffy_b64}"',
        html
    )

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("\n🎉 SUCCESS! All 3 photos are now embedded directly inside static/index.html!")