#!/usr/bin/env python3
"""
generate_icons.py
Resizes the source icon into the sizes Chrome expects and
saves them into extension/icons/.

Usage:  python3 generate_icons.py
Requires: pip install Pillow
"""
import os
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Pillow not found. Run:  pip install Pillow")

# --- paths ---
SCRIPT_DIR  = Path(__file__).parent
SRC         = SCRIPT_DIR / "extension" / "icons" / "icon_source.png"
ICONS_DIR   = SCRIPT_DIR / "extension" / "icons"
SIZES       = [16, 48, 128]

# If the source hasn't been placed yet, look for the generated PNG
# alongside this script (the AI-generated icon).
if not SRC.exists():
    candidates = list(SCRIPT_DIR.glob("vaani_icon*.png"))
    if candidates:
        import shutil
        ICONS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(candidates[0], SRC)
        print(f"Copied {candidates[0].name} → extension/icons/icon_source.png")
    else:
        raise SystemExit(
            f"Source icon not found.\n"
            f"Place a square PNG at:  {SRC}\n"
            f"or put any PNG named vaani_icon*.png next to this script."
        )

ICONS_DIR.mkdir(parents=True, exist_ok=True)
img = Image.open(SRC).convert("RGBA")

for size in SIZES:
    out_path = ICONS_DIR / f"icon{size}.png"
    resized  = img.resize((size, size), Image.LANCZOS)
    resized.save(out_path, "PNG")
    print(f"  ✓ icon{size}.png")

print("\nAll icons generated in extension/icons/")
