"""Simple flat illustrations and picture placeholders, drawn with Pillow.

The templates use the placeholders ("Your photo here"); the fictional sample
organisation uses the illustrations in place of real photos. Everything is
drawn at three times the size and then scaled down, which smooths the edges.
"""

from __future__ import annotations

import io
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCALE = 3

_FONT_FILES = {
    "sans": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf", "arial.ttf"],
    "sans-bold": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial Bold.ttf",
                  "arialbd.ttf"],
    "serif-bold": ["Caladea-Bold.ttf", "LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf",
                   "Georgia Bold.ttf", "georgiab.ttf"],
}
_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/liberation2", "/usr/share/fonts/truetype/crosextra",
    "/usr/share/fonts/truetype", "/Library/Fonts", "/System/Library/Fonts/Supplemental",
    "C:/Windows/Fonts",
]


def font(kind: str, size: int):
    for name in _FONT_FILES.get(kind, _FONT_FILES["sans"]):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
        for folder in _FONT_DIRS:
            path = Path(folder) / name
            if path.exists():
                return ImageFont.truetype(str(path), size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow older than 10.1
        return ImageFont.load_default()


def rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(a, b, t: float) -> tuple[int, int, int]:
    a, b = (rgb(a) if isinstance(a, str) else a), (rgb(b) if isinstance(b, str) else b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


class Canvas:
    """A drawing surface in final pixel units, drawn at SCALE x for smoothness."""

    def __init__(self, width: int, height: int, background="FFFFFF"):
        """background=None gives a transparent picture (for logos)."""
        self.w, self.h = width, height
        if background is None:
            self.img = Image.new("RGBA", (width * SCALE, height * SCALE), (255, 255, 255, 0))
        else:
            bg = rgb(background) if isinstance(background, str) else background
            self.img = Image.new("RGB", (width * SCALE, height * SCALE), bg)
        self.d = ImageDraw.Draw(self.img)

    def _s(self, values):
        return [v * SCALE for v in values]

    def gradient(self, top, bottom, box=None):
        x0, y0, x1, y1 = box or (0, 0, self.w, self.h)
        for y in range(int(y0 * SCALE), int(y1 * SCALE)):
            t = (y - y0 * SCALE) / max(1, (y1 - y0) * SCALE - 1)
            self.d.line([(x0 * SCALE, y), (x1 * SCALE - 1, y)], fill=mix(top, bottom, t))

    def rect(self, box, fill=None, outline=None, width=1, radius=0):
        fill = rgb(fill) if isinstance(fill, str) else fill
        outline = rgb(outline) if isinstance(outline, str) else outline
        if radius:
            self.d.rounded_rectangle(self._s(box), radius=radius * SCALE, fill=fill,
                                     outline=outline, width=int(width * SCALE))
        else:
            self.d.rectangle(self._s(box), fill=fill, outline=outline, width=int(width * SCALE))

    def ellipse(self, box, fill=None, outline=None, width=1):
        fill = rgb(fill) if isinstance(fill, str) else fill
        outline = rgb(outline) if isinstance(outline, str) else outline
        self.d.ellipse(self._s(box), fill=fill, outline=outline, width=int(width * SCALE))

    def circle(self, cx, cy, r, fill=None, outline=None, width=1):
        self.ellipse((cx - r, cy - r, cx + r, cy + r), fill, outline, width)

    def poly(self, points, fill=None, outline=None, width=1):
        fill = rgb(fill) if isinstance(fill, str) else fill
        outline = rgb(outline) if isinstance(outline, str) else outline
        pts = [(x * SCALE, y * SCALE) for x, y in points]
        self.d.polygon(pts, fill=fill, outline=outline, width=int(width * SCALE))

    def line(self, points, fill, width=1):
        fill = rgb(fill) if isinstance(fill, str) else fill
        pts = [(x * SCALE, y * SCALE) for x, y in points]
        self.d.line(pts, fill=fill, width=max(1, int(width * SCALE)), joint="curve")

    def arc(self, box, start, end, fill, width=1):
        fill = rgb(fill) if isinstance(fill, str) else fill
        self.d.arc(self._s(box), start, end, fill=fill, width=int(width * SCALE))

    def text(self, xy, text, size, fill, kind="sans", anchor="mm"):
        fill = rgb(fill) if isinstance(fill, str) else fill
        self.d.text((xy[0] * SCALE, xy[1] * SCALE), text, font=font(kind, size * SCALE),
                    fill=fill, anchor=anchor)

    def png(self) -> bytes:
        out = self.img.resize((self.w, self.h), Image.LANCZOS)
        buffer = io.BytesIO()
        out.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()


# ---------------------------------------------------------------------------
# Placeholders for the blank templates
# ---------------------------------------------------------------------------

def placeholder(width: int, height: int, label: str, hint: str = "",
                kind: str = "photo", tint="EEF2F7", ink="1F3A5F") -> bytes:
    c = Canvas(width, height, tint)
    dash, gap = 14, 9
    inset = 6
    for x in range(inset, width - inset, dash + gap):
        c.line([(x, inset), (min(x + dash, width - inset), inset)], ink, 2)
        c.line([(x, height - inset), (min(x + dash, width - inset), height - inset)], ink, 2)
    for y in range(inset, height - inset, dash + gap):
        c.line([(inset, y), (inset, min(y + dash, height - inset))], ink, 2)
        c.line([(width - inset, y), (width - inset, min(y + dash, height - inset))], ink, 2)
    cx, cy = width / 2, height / 2 - (14 if hint else 6)
    s = min(width, height) * 0.16
    if kind == "photo":
        c.rect((cx - s * 1.4, cy - s, cx + s * 1.4, cy + s * 0.9), outline=ink, width=3, radius=6)
        c.poly([(cx - s * 1.2, cy + s * 0.7), (cx - s * 0.4, cy - s * 0.2), (cx + s * 0.1, cy + s * 0.4),
                (cx + s * 0.5, cy), (cx + s * 1.2, cy + s * 0.7)], fill=mix(ink, tint, 0.55))
        c.circle(cx + s * 0.75, cy - s * 0.45, s * 0.22, fill=mix(ink, tint, 0.55))
    elif kind == "logo":
        c.circle(cx, cy, s * 1.1, outline=ink, width=3)
        c.text((cx, cy), "LOGO", int(s * 0.55), ink, "sans-bold")
    elif kind == "qr":
        q = s * 0.9
        c.rect((cx - q, cy - q, cx + q, cy + q), outline=ink, width=3)
        for (gx, gy) in ((-1, -1), (1, -1), (-1, 1)):
            x0, y0 = cx + gx * q * 0.55, cy + gy * q * 0.55
            c.rect((x0 - q * 0.3, y0 - q * 0.3, x0 + q * 0.3, y0 + q * 0.3), fill=ink)
        c.rect((cx + q * 0.25, cy + q * 0.25, cx + q * 0.45, cy + q * 0.45), fill=ink)
    label_y = cy + s * 1.35 + 10
    c.text((cx, label_y), label, max(11, int(min(width, height) * 0.075)), ink, "sans-bold")
    if hint:
        c.text((cx, label_y + max(14, int(min(width, height) * 0.08))), hint,
               max(9, int(min(width, height) * 0.05)), mix(ink, tint, 0.3))
    return c.png()


# ---------------------------------------------------------------------------
# Illustrations for the fictional sample organisation
# ---------------------------------------------------------------------------

def church_scene(width=900, height=560) -> bytes:
    c = Canvas(width, height)
    c.gradient("BFDDF2", "F4EFD9", (0, 0, width, height * 0.75))
    c.circle(width * 0.8, height * 0.22, height * 0.09, fill="FFE9A8")
    c.ellipse((-width * 0.2, height * 0.55, width * 0.7, height * 1.2), fill="9CC08A")
    c.ellipse((width * 0.3, height * 0.6, width * 1.3, height * 1.25), fill="7FAF6E")
    c.rect((0, height * 0.82, width, height), fill="6A9C5B")
    # church
    base_y = height * 0.82
    nave = (width * 0.42, height * 0.5, width * 0.78, base_y)
    c.rect(nave, fill="D9D1C0")
    c.poly([(width * 0.40, height * 0.5), (width * 0.60, height * 0.33), (width * 0.80, height * 0.5)],
           fill="5B6472")
    tower = (width * 0.30, height * 0.36, width * 0.42, base_y)
    c.rect(tower, fill="CFC6B3")
    c.poly([(width * 0.29, height * 0.36), (width * 0.36, height * 0.12), (width * 0.43, height * 0.36)],
           fill="4E5664")
    c.line([(width * 0.36, height * 0.12), (width * 0.36, height * 0.05)], "4E5664", 3)
    c.line([(width * 0.345, height * 0.075), (width * 0.375, height * 0.075)], "4E5664", 3)
    # door and windows
    c.rect((width * 0.345, height * 0.68, width * 0.375, base_y), fill="7A4E2D")
    c.ellipse((width * 0.345, height * 0.655, width * 0.375, height * 0.705), fill="7A4E2D")
    for i in range(3):
        x = width * (0.48 + i * 0.1)
        c.rect((x, height * 0.6, x + width * 0.035, height * 0.72), fill="5E7FA3")
        c.ellipse((x, height * 0.58, x + width * 0.035, height * 0.62), fill="5E7FA3")
    c.circle(width * 0.36, height * 0.46, width * 0.018, fill="5E7FA3")
    # trees and path
    for tx, r in ((0.12, 0.09), (0.2, 0.065), (0.9, 0.08)):
        c.rect((width * tx - 4, height * 0.68, width * tx + 4, base_y), fill="6B4F35")
        c.circle(width * tx, height * 0.64, height * r * 1.2, fill="4F8A4A")
    c.poly([(width * 0.345, base_y), (width * 0.375, base_y), (width * 0.46, height),
            (width * 0.26, height)], fill="E8DDC4")
    return c.png()


def flowers_scene(width=900, height=560) -> bytes:
    c = Canvas(width, height)
    c.gradient("E4F3E8", "FFF8E7")
    c.rect((0, height * 0.78, width, height), fill="8DBF7B")
    colours = ["E58FA8", "F2C14E", "B48ED1", "F28C6B", "7FB3E0"]
    for i in range(11):
        x = width * (0.06 + i * 0.088)
        top = height * (0.32 + 0.12 * math.sin(i * 1.7))
        c.line([(x, height * 0.92), (x + 6 * math.sin(i), top)], "4E8A45", 4)
        c.ellipse((x - 26, top + 40, x - 2, top + 58), fill="5E9E52")
        colour = colours[i % len(colours)]
        if i % 3 == 0:  # tulip
            c.poly([(x - 22, top - 8), (x - 14, top - 34), (x, top - 16), (x + 14, top - 34),
                    (x + 22, top - 8), (x + 16, top + 16), (x - 16, top + 16)], fill=colour)
        else:
            for k in range(6):
                a = k * math.pi / 3
                c.circle(x + 18 * math.cos(a), top + 18 * math.sin(a), 15, fill=colour)
            c.circle(x, top, 11, fill="FFE08A")
    for bx, by in ((0.25, 0.18), (0.7, 0.12)):
        x, y = width * bx, height * by
        c.ellipse((x - 26, y - 16, x, y + 14), fill="F2A65A")
        c.ellipse((x, y - 16, x + 26, y + 14), fill="F2A65A")
        c.line([(x, y - 14), (x, y + 14)], "5A4632", 3)
    return c.png()


def harvest_scene(width=900, height=560) -> bytes:
    c = Canvas(width, height)
    c.gradient("FBE7C6", "F6D59A")
    c.rect((0, height * 0.8, width, height), fill="B5835A")
    # wheat sheaf
    cx, base = width * 0.3, height * 0.82
    for k in range(-6, 7):
        top_x = cx + k * 16
        top_y = height * 0.2 + abs(k) * 8
        c.line([(cx + k * 3, base), (top_x, top_y)], "C99A3B", 4)
        for j in range(6):
            gy = top_y + j * 13
            gx = top_x + (cx + k * 3 - top_x) * (j * 13) / (base - top_y)
            c.ellipse((gx - 9, gy - 5, gx - 1, gy + 7), fill="E2B24F")
            c.ellipse((gx + 1, gy - 5, gx + 9, gy + 7), fill="E2B24F")
    c.rect((cx - 40, height * 0.58, cx + 40, height * 0.63), fill="8B5A2B")
    # pumpkins and apples
    for px, pr, col in ((0.62, 0.15, "E07B2E"), (0.82, 0.11, "EA9441")):
        x, r = width * px, height * pr
        y = height * 0.8 - r * 0.8
        for dx in (-0.55, 0, 0.55):
            c.ellipse((x + dx * r - r * 0.6, y - r * 0.8, x + dx * r + r * 0.6, y + r * 0.8), fill=col)
        c.rect((x - 5, y - r * 0.95, x + 5, y - r * 0.7), fill="5E7A34")
    for ax in (0.5, 0.55, 0.72):
        x, y = width * ax, height * 0.76
        c.circle(x, y, 22, fill="C8372D")
        c.ellipse((x + 2, y - 34, x + 18, y - 22), fill="5E9E52")
    return c.png()


def bunting_scene(width=900, height=560) -> bytes:
    c = Canvas(width, height)
    c.gradient("BFE3F5", "F3FAFD")
    c.rect((0, height * 0.8, width, height), fill="8CC37A")
    colours = ["E4572E", "F3A712", "29A3A3", "6C4AB6", "E84E8A", "3E8E41"]
    for row, depth in ((0, 0.16), (1, 0.3)):
        y0 = height * (0.05 + row * 0.12)
        pts = [(x, y0 + math.sin(math.pi * x / width) * height * depth * 0.35)
               for x in range(0, width + 1, 10)]
        c.line(pts, "666666", 2)
        for i, x in enumerate(range(20, width - 20, 70)):
            y = y0 + math.sin(math.pi * x / width) * height * depth * 0.35
            c.poly([(x - 22, y), (x + 22, y), (x, y + 46)], fill=colours[(i + row) % len(colours)])
    # marquee tent
    tx, ty, tw = width * 0.5, height * 0.42, width * 0.42
    c.poly([(tx - tw / 2, ty + 70), (tx, ty), (tx + tw / 2, ty + 70)], fill="FFFFFF")
    for k in range(6):
        x0 = tx - tw / 2 + k * tw / 6
        if k % 2 == 0:
            c.poly([(x0, ty + 70), (tx, ty), (x0 + tw / 6, ty + 70)], fill="D64545")
    c.rect((tx - tw / 2, ty + 70, tx + tw / 2, height * 0.8), fill="FFFFFF")
    for k in range(0, 6, 2):
        x0 = tx - tw / 2 + k * tw / 6
        c.rect((x0, ty + 70, x0 + tw / 6, height * 0.8), fill="D64545")
    c.rect((tx - 30, height * 0.62, tx + 30, height * 0.8), fill="7A4E2D")
    c.line([(tx, ty), (tx, ty - 40)], "555555", 3)
    c.poly([(tx, ty - 40), (tx + 30, ty - 30), (tx, ty - 20)], fill="F3A712")
    return c.png()


def candles_scene(width=900, height=560) -> bytes:
    c = Canvas(width, height)
    c.gradient("1B2A4A", "2F4A7A")
    for i in range(40):
        x = (i * 137) % width
        y = (i * 71) % int(height * 0.55)
        c.circle(x, y, 1.6 + (i % 3), fill="F4E7B2")
    c.ellipse((width * 0.12, height * 0.78, width * 0.88, height * 0.98), fill="2E6B3A")
    colours = ["7E57C2", "7E57C2", "E57399", "7E57C2"]
    for i, col in enumerate(colours):
        x = width * (0.24 + i * 0.17)
        h = height * (0.32 + 0.04 * (i % 2))
        top = height * 0.84 - h
        for k, r in enumerate((54, 44, 34)):
            c.circle(x, top - 30, r, fill=mix("22365C", "F7D774", 0.12 + k * 0.1))
        c.rect((x - 26, top, x + 26, height * 0.86), fill=col, radius=4)
        c.ellipse((x - 10, top - 52, x + 10, top - 8), fill="F7B733")
        c.ellipse((x - 5, top - 36, x + 5, top - 12), fill="FFF2C2")
    for hx in (0.17, 0.5, 0.83):
        x = width * hx
        c.ellipse((x - 40, height * 0.84, x, height * 0.9), fill="3F8F4F")
        c.ellipse((x, height * 0.84, x + 40, height * 0.9), fill="3F8F4F")
        c.circle(x, height * 0.85, 8, fill="C62828")
    return c.png()


def books_scene(width=900, height=560) -> bytes:
    c = Canvas(width, height)
    c.gradient("FFF4E0", "FDE3C3")
    colours = ["2F6690", "D1495B", "EDAE49", "00798C", "6A4C93"]
    y = height * 0.9
    for i, col in enumerate(colours):
        h = 46 + (i % 2) * 10
        w = width * (0.5 - i * 0.03)
        x = width * 0.25 + (i % 2) * 14
        c.rect((x, y - h, x + w, y), fill=col, radius=6)
        c.rect((x + 10, y - h + 10, x + w - 10, y - h + 16), fill=mix(col, "FFFFFF", 0.4))
        y -= h + 2
    # open book
    bx, by = width * 0.5, y - 10
    c.poly([(bx, by), (bx - 170, by - 40), (bx - 170, by - 150), (bx, by - 110)], fill="FFFFFF",
           outline="8A6D3B", width=3)
    c.poly([(bx, by), (bx + 170, by - 40), (bx + 170, by - 150), (bx, by - 110)], fill="FFFFFF",
           outline="8A6D3B", width=3)
    for k in range(4):
        c.line([(bx - 150, by - 135 + k * 22 + 0), (bx - 20, by - 100 + k * 22)], "C9B79C", 3)
        c.line([(bx + 20, by - 100 + k * 22), (bx + 150, by - 135 + k * 22)], "C9B79C", 3)
    for sx, sy, r in ((0.15, 0.2, 26), (0.85, 0.25, 30), (0.78, 0.08, 18), (0.2, 0.5, 16)):
        cx, cy = width * sx, height * sy
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        c.poly(pts, fill="F2B632")
    return c.png()


def coffee_scene(width=900, height=560) -> bytes:
    c = Canvas(width, height)
    c.gradient("F7EDE2", "EAD7C3")
    c.rect((0, height * 0.78, width, height), fill="C8A27A")
    cx, cy = width * 0.38, height * 0.55
    c.ellipse((cx - 160, height * 0.74, cx + 160, height * 0.84), fill="FFFFFF")
    c.rect((cx - 110, cy - 80, cx + 110, cy + 110), fill="FFFFFF", radius=30)
    c.ellipse((cx + 90, cy - 40, cx + 170, cy + 60), outline="FFFFFF", width=18)
    c.ellipse((cx - 104, cy - 96, cx + 104, cy - 64), fill="7B4A2D")
    for k in (-50, 0, 50):
        pts = [(cx + k + 12 * math.sin(t / 12), cy - 110 - t) for t in range(0, 110, 4)]
        c.line(pts, "B9A08A", 6)
    # cake slice
    kx, ky = width * 0.72, height * 0.74
    c.poly([(kx - 110, ky), (kx + 110, ky), (kx + 110, ky - 110)], fill="F6D9A7")
    c.poly([(kx - 110, ky - 6), (kx + 110, ky - 6), (kx + 110, ky - 40), (kx - 60, ky - 30)],
           fill="E8A0B4")
    c.poly([(kx - 30, ky - 50), (kx + 110, ky - 50), (kx + 110, ky - 70), (kx + 10, ky - 70)],
           fill="FFFFFF")
    c.circle(kx + 80, ky - 125, 14, fill="C62828")
    return c.png()


def window_scene(width=700, height=860, colours=None) -> bytes:
    """An arched window for a service-sheet cover."""
    colours = colours or ["F2C14E", "E07A5F", "3D5A80", "81B29A", "98C1D9"]
    c = Canvas(width, height, "FFFFFF")
    pad = 40
    x0, x1 = pad, width - pad
    arch_r = (x1 - x0) / 2
    top = pad + arch_r
    # glass: horizontal bands, then lead lines
    c.gradient("FFF3D6", "DCEAF5", (x0, pad, x1, height - pad))
    rows, cols = 7, 3
    cell_w = (x1 - x0) / cols
    cell_h = (height - pad - top) / rows
    for r in range(rows):
        for k in range(cols):
            col = colours[(r * 2 + k) % len(colours)]
            bx0, by0 = x0 + k * cell_w, top + r * cell_h
            c.rect((bx0 + 6, by0 + 6, bx0 + cell_w - 6, by0 + cell_h - 6),
                   fill=mix(col, "FFFFFF", 0.35))
    for k in range(5):
        a0 = 180 + k * 36
        c.d.pieslice([((width / 2) - arch_r + 6) * SCALE, (pad + 6) * SCALE,
                      ((width / 2) + arch_r - 6) * SCALE, (pad + 2 * arch_r - 6) * SCALE],
                     a0, a0 + 36, fill=mix(colours[k % len(colours)], "FFFFFF", 0.3))
    c.circle(width / 2, top, arch_r * 0.32, fill=mix(colours[0], "FFFFFF", 0.1))
    lead = "3B3B3B"
    c.arc((x0, pad, x1, pad + 2 * arch_r), 180, 360, lead, 10)
    c.line([(x0, top), (x0, height - pad), (x1, height - pad), (x1, top)], lead, 10)
    for k in range(1, cols):
        c.line([(x0 + k * cell_w, top), (x0 + k * cell_w, height - pad)], lead, 6)
    for r in range(1, rows):
        c.line([(x0, top + r * cell_h), (x1, top + r * cell_h)], lead, 4)
    c.line([(x0, top), (x1, top)], lead, 6)
    c.circle(width / 2, top, arch_r * 0.32, outline=lead, width=6)
    return c.png()


def emblem(initials: str, primary="1F3A5F", accent="C8912E", size=600) -> bytes:
    """A round logo: church outline above the initials, on a clear background."""
    c = Canvas(size, size, None)
    c.circle(size / 2, size / 2, size * 0.48, fill=primary)
    c.circle(size / 2, size / 2, size * 0.43, outline=accent, width=size * 0.012)
    s = size / 600
    c.rect((250 * s, 230 * s, 350 * s, 330 * s), fill="FFFFFF")
    c.poly([(240 * s, 232 * s), (300 * s, 180 * s), (360 * s, 232 * s)], fill="FFFFFF")
    c.rect((292 * s, 120 * s, 308 * s, 182 * s), fill=accent)
    c.rect((276 * s, 136 * s, 324 * s, 150 * s), fill=accent)
    c.rect((288 * s, 280 * s, 312 * s, 330 * s), fill=primary)
    c.text((size / 2, size * 0.68), initials, int(size * 0.17), "FFFFFF", "serif-bold")
    return c.png()


SCENES = {
    "church": church_scene,
    "flowers": flowers_scene,
    "harvest": harvest_scene,
    "bunting": bunting_scene,
    "candles": candles_scene,
    "books": books_scene,
    "coffee": coffee_scene,
    "window": window_scene,
}


def picture(spec: str, base_dir: Path | None = None, brand: dict | None = None) -> bytes:
    """Turn "art:church", "art:emblem:SA" or a file path into PNG/JPEG bytes."""
    if spec.startswith("art:emblem"):
        initials = spec.split(":", 2)[2] if spec.count(":") >= 2 else "A"
        brand = brand or {}
        return emblem(initials, brand.get("primary", "1F3A5F"), brand.get("accent", "C8912E"))
    if spec.startswith("art:"):
        return SCENES[spec[4:]]()
    path = Path(spec)
    if base_dir and not path.is_absolute():
        path = base_dir / path
    return path.read_bytes()


if __name__ == "__main__":  # preview every illustration: python artwork.py out_dir
    import sys

    out = Path(sys.argv[1] if len(sys.argv) > 1 else "artwork-preview")
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in SCENES.items():
        (out / f"{name}.png").write_bytes(fn())
    (out / "emblem.png").write_bytes(emblem("St A"))
    (out / "placeholder-photo.png").write_bytes(
        placeholder(800, 500, "Your photo here", "Right-click > Change Picture"))
    (out / "placeholder-logo.png").write_bytes(placeholder(400, 400, "Your logo", kind="logo"))
    (out / "placeholder-qr.png").write_bytes(placeholder(300, 300, "QR code", kind="qr"))
    print(f"Wrote previews to {out}")
