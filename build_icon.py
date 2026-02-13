#!/usr/bin/env python3
"""Generate macOS .icns icon for UnityPy Explorer."""

import os
import struct
import io

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow required: pip install Pillow")
    exit(1)


def create_icon_image(size: int) -> Image.Image:
    """Create a single icon image at the given size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background: rounded rectangle
    margin = int(size * 0.05)
    radius = int(size * 0.18)
    # Dark gradient-like background
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=(30, 30, 46, 255),       # base color #1e1e2e
        outline=(69, 71, 90, 255),     # surface1 #45475a
        width=max(1, size // 128),
    )

    # Inner accent bar at top
    bar_h = int(size * 0.06)
    draw.rounded_rectangle(
        [margin, margin, size - margin, margin + bar_h + radius],
        radius=radius,
        fill=(137, 180, 250, 255),  # blue #89b4fa
    )
    # Clip bottom of bar to be straight
    draw.rectangle(
        [margin, margin + bar_h, size - margin, margin + bar_h + radius],
        fill=(30, 30, 46, 255),
    )

    # "U" letter in center (skip text for very small sizes)
    if size >= 32:
        font_size = max(10, int(size * 0.45))
        font = None
        for font_path in [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFCompact.ttf",
            "/System/Library/Fonts/SFNS.ttf",
        ]:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except (OSError, IOError):
                continue
        if font is None:
            font = ImageFont.load_default()

        text = "U"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (size - tw) // 2
        ty = (size - th) // 2 + int(size * 0.04)
        draw.text((tx, ty), text, fill=(137, 180, 250, 255), font=font)

        # Small "Py" subscript
        if size >= 64:
            sub_size = max(8, int(size * 0.16))
            try:
                sub_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", sub_size)
            except (OSError, IOError):
                sub_font = font
            sub_text = "Py"
            sx = tx + tw + int(size * 0.01)
            sy = ty + th - int(size * 0.15)
            draw.text((sx, sy), sub_text, fill=(166, 227, 161, 255), font=sub_font)
    else:
        # For tiny icons, just draw a centered blue square
        c = size // 2
        r = size // 5
        draw.rounded_rectangle(
            [c - r, c - r, c + r, c + r],
            radius=max(1, r // 3),
            fill=(137, 180, 250, 255),
        )

    # Decorative squares at bottom
    if size >= 64:
        d = int(size * 0.05)
        positions = [
            (int(size * 0.15), int(size * 0.78)),
            (int(size * 0.28), int(size * 0.84)),
            (int(size * 0.72), int(size * 0.78)),
            (int(size * 0.85), int(size * 0.84)),
        ]
        colors = [
            (243, 139, 168, 200),  # red
            (250, 179, 135, 200),  # peach
            (203, 166, 247, 200),  # mauve
            (148, 226, 213, 200),  # teal
        ]
        for (px, py), col in zip(positions, colors):
            draw.rounded_rectangle(
                [px - d, py - d, px + d, py + d],
                radius=max(1, d // 3),
                fill=col,
            )

    return img


def images_to_icns(images: dict[int, Image.Image], output_path: str):
    """
    Convert a dict of {size: PIL.Image} to an .icns file.
    Uses PNG encoding for each icon size (supported on macOS 10.7+).
    """
    # ICNS icon type codes for PNG-encoded icons
    icon_types = {
        16:   b'icp4',   # 16x16
        32:   b'icp5',   # 32x32
        64:   b'icp6',   # 64x64
        128:  b'ic07',   # 128x128
        256:  b'ic08',   # 256x256
        512:  b'ic09',   # 512x512
        1024: b'ic10',   # 1024x1024 (512x512@2x)
    }

    entries = []
    for size, img in sorted(images.items()):
        if size not in icon_types:
            continue
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_data = buf.getvalue()
        icon_type = icon_types[size]
        # Each entry: type (4 bytes) + length (4 bytes) + data
        entry_len = 8 + len(png_data)
        entries.append(struct.pack(">4sI", icon_type, entry_len) + png_data)

    # ICNS file: header (magic 'icns' + total file length) + entries
    body = b"".join(entries)
    total_len = 8 + len(body)
    icns_data = struct.pack(">4sI", b"icns", total_len) + body

    with open(output_path, "wb") as f:
        f.write(icns_data)


def main():
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    images = {}
    for s in sizes:
        print(f"  Generating {s}x{s}...")
        images[s] = create_icon_image(s)

    # Save as .icns
    icns_path = os.path.join(os.path.dirname(__file__), "UnityPyExplorer.icns")
    images_to_icns(images, icns_path)
    print(f"Icon saved: {icns_path}")

    # Also save a PNG preview
    png_path = os.path.join(os.path.dirname(__file__), "UnityPyExplorer_icon.png")
    images[512].save(png_path)
    print(f"PNG preview saved: {png_path}")


if __name__ == "__main__":
    main()
