import os
import re

static_dir = "static"
html_path = os.path.join(static_dir, "index.html")

if not os.path.exists(html_path):
    print("❌ Error: static/index.html not found!")
    exit()

files = os.listdir(static_dir)
print("📁 All files found inside static/ folder:")
for f in files:
    print("   -", f)

def find_file(keyword):
    for f in files:
        if keyword in f.lower() and f.lower() != "index.html":
            return f
    return None

luffy_file = find_file("luffy")
zoro_file = find_file("zoro")
nami_file = find_file("nami")

print("\n🔍 Image Matching Results:")
print(f"   Luffy -> {luffy_file}")
print(f"   Zoro  -> {zoro_file}")
print(f"   Nami  -> {nami_file}")

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# Replace images with exact detected filenames
if zoro_file:
    html = re.sub(r'src="/static/[^"]*zoro[^"]*"', f'src="/static/{zoro_file}"', html, flags=re.I)
if nami_file:
    html = re.sub(r'src="/static/[^"]*nami[^"]*"', f'src="/static/{nami_file}"', html, flags=re.I)
if luffy_file:
    html = re.sub(r'src="/static/[^"]*luffy[^"]*"', f'src="/static/{luffy_file}"', html, flags=re.I)

# Also fix modal poster image
if luffy_file:
    html = re.sub(r'src="/static/[^"]*luffy[^"]*"', f'src="/static/{luffy_file}"', html, flags=re.I)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print("\n✨ Updated static/index.html with exact image paths!")