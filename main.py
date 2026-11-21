"""The World in One Image - Friday 20 November 2026.

A self-contained newspaper front page that sums up the world's news of
Friday 20 November 2026 in a single picture. Pure Python standard library:
the program carries its own tiny bitmap font and its own PNG writer, draws
the page with simple shapes, and writes the result to entry.png in the
output directory ($MAKEFUN_OUTPUT_DIR, or /output when run by the grader).
The drawing is fully deterministic: two runs write the same bytes.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (246, 241, 231)
INK = (23, 35, 59)
CARD = (255, 253, 248)
RED = (200, 16, 46)
NAVY = (23, 35, 59)
GOLD = (183, 149, 11)
WHITE = (250, 248, 242)
GREY = (96, 104, 118)

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 bits, top row first.
# ---------------------------------------------------------------------------
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1C, 0x12, 0x11, 0x11, 0x11, 0x12, 0x1C),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x0A, 0x04, 0x04, 0x04, 0x0A, 0x11),
    "Y": (0x11, 0x0A, 0x04, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "-": (0x00, 0x00, 0x00, 0x0E, 0x00, 0x00, 0x00),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04),
    "%": (0x19, 0x1A, 0x02, 0x04, 0x08, 0x0B, 0x13),
    "+": (0x00, 0x04, 0x04, 0x0E, 0x04, 0x04, 0x00),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1D, 0x04),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '"': (0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00),
}


# ---------------------------------------------------------------------------
# Canvas: a plain RGB framebuffer plus drawing primitives.
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect_outline(self, x, y, w, h, color, t=2):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def fill_circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dx = int(math.sqrt(max(0, r * r - (yy - cy) * (yy - cy))))
            self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, color)

    def ring(self, cx, cy, r, color, t=3):
        steps = max(24, int(2 * math.pi * r))
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            self.fill_rect(x - t // 2, y - t // 2, t, t, color)

    def arc(self, cx, cy, r, a0, a1, color, t=3):
        steps = max(12, int(abs(a1 - a0) * r))
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            self.fill_rect(x - t // 2, y - t // 2, t, t, color)

    def line(self, x0, y0, x1, y1, color, t=3):
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            x = int(round(x0 + dx * i / steps))
            y = int(round(y0 + dy * i / steps))
            self.fill_rect(x - t // 2, y - t // 2, t, t, color)

    def fill_poly(self, pts, color):
        ys = [p[1] for p in pts]
        y_lo = max(0, int(min(ys)))
        y_hi = min(self.h - 1, int(max(ys)))
        n = len(pts)
        for yy in range(y_lo, y_hi + 1):
            xs = []
            for i in range(n):
                xa, ya = pts[i]
                xb, yb = pts[(i + 1) % n]
                if ya == yb:
                    continue
                if (ya <= yy < yb) or (yb <= yy < ya):
                    xs.append(xa + (yy - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), yy, int(xs[i + 1]) - int(xs[i]) + 1, 1, color)

    # -- text ---------------------------------------------------------------
    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, x, y, s, scale, color):
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.fill_rect(x + col * scale, y + row * scale,
                                       scale, scale, color)
            x += 6 * scale

    def text_centered(self, cx, y, s, scale, color):
        self.text(cx - self.text_width(s, scale) // 2, y, s, scale, color)


def star_points(cx, cy, r_out, r_in, n=5, rot=-math.pi / 2):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# ---------------------------------------------------------------------------
# Icons. Each is drawn inside a box centred on (cx, cy).
# ---------------------------------------------------------------------------
def icon_drone(cv, cx, cy):
    ink = INK
    for dx, dy in ((-30, -24), (30, -24), (-30, 24), (30, 24)):
        cv.line(cx, cy, cx + dx, cy + dy, ink, 4)
        cv.ring(cx + dx, cy + dy, 11, ink, 3)
    cv.fill_rect(cx - 15, cy - 10, 30, 20, ink)
    cv.fill_circle(cx, cy + 16, 5, RED)
    burst = star_points(cx + 34, cy + 34, 17, 7, 8, 0.2)
    cv.fill_poly(burst, (232, 126, 34))
    cv.fill_circle(cx + 34, cy + 34, 6, (241, 196, 15))


def icon_scales(cv, cx, cy):
    ink = INK
    cv.fill_rect(cx - 3, cy - 34, 6, 62, ink)
    cv.fill_rect(cx - 34, cy - 34, 68, 5, ink)
    cv.fill_circle(cx, cy - 36, 6, GOLD)
    for side in (-1, 1):
        px = cx + side * 30
        cv.line(px, cy - 31, px - 11, cy - 4, ink, 3)
        cv.line(px, cy - 31, px + 11, cy - 4, ink, 3)
        cv.arc(px, cy - 16, 13, 0.15 * math.pi, 0.85 * math.pi, ink, 4)
        cv.fill_rect(px - 13, cy - 5, 26, 4, ink)
    cv.fill_rect(cx - 18, cy + 28, 36, 6, ink)
    cv.fill_rect(cx - 8, cy + 20, 16, 8, ink)


def icon_chart(cv, cx, cy):
    ink = INK
    cv.line(cx - 36, cy - 34, cx - 36, cy + 32, ink, 3)
    cv.line(cx - 36, cy + 32, cx + 38, cy + 32, ink, 3)
    for gy in (-12, 8):
        cv.line(cx - 36, cy + gy, cx + 36, cy + gy, (196, 202, 212), 2)
    pts = [(cx - 30, cy - 26), (cx - 12, cy - 14), (cx + 2, cy - 20),
           (cx + 16, cy - 2), (cx + 32, cy + 22)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 5)
    cv.fill_poly([(cx + 32, cy + 24), (cx + 18, cy + 20), (cx + 27, cy + 10)], RED)


def icon_ship(cv, cx, cy):
    ink = INK
    cv.fill_poly([(cx - 38, cy + 2), (cx + 38, cy + 2),
                  (cx + 28, cy + 20), (cx - 28, cy + 20)], (176, 58, 46))
    cv.fill_rect(cx - 30, cy - 12, 20, 14, (26, 82, 118))
    cv.fill_rect(cx - 6, cy - 12, 20, 14, (30, 132, 73))
    cv.fill_rect(cx + 18, cy - 12, 16, 14, GOLD)
    cv.fill_rect(cx + 22, cy - 26, 12, 14, ink)
    for i in range(5):
        wx = cx - 36 + i * 18
        cv.arc(wx + 8, cy + 30, 8, math.pi, 2 * math.pi, (26, 82, 118), 3)
    cv.fill_circle(cx + 34, cy - 28, 7, ink)
    for a in range(8):
        ang = a * math.pi / 4
        cv.line(cx + 34 + int(9 * math.cos(ang)), cy - 28 + int(9 * math.sin(ang)),
                cx + 34 + int(13 * math.cos(ang)), cy - 28 + int(13 * math.sin(ang)), ink, 3)


def icon_leaf(cv, cx, cy):
    green = (30, 132, 73)
    pts = []
    for i in range(25):
        t = i / 24
        pts.append((cx - 30 + 60 * t, cy + 24 - 52 * t + 16 * math.sin(t * math.pi)))
    for i in range(24, -1, -1):
        t = i / 24
        pts.append((cx - 30 + 60 * t, cy + 24 - 52 * t - 16 * math.sin(t * math.pi)))
    cv.fill_poly(pts, green)
    cv.line(cx - 30, cy + 26, cx + 30, cy - 28, (20, 90, 50), 4)
    cv.line(cx - 30, cy + 26, cx - 40, cy + 36, (20, 90, 50), 4)


def icon_frame(cv, cx, cy):
    cv.fill_rect(cx - 34, cy - 36, 68, 72, GOLD)
    cv.fill_rect(cx - 27, cy - 29, 54, 58, (25, 42, 86))
    cv.fill_poly(star_points(cx - 8, cy - 8, 11, 5), (241, 196, 15))
    cv.fill_poly(star_points(cx + 13, cy + 12, 7, 3), (241, 196, 15))
    cv.arc(cx + 8, cy - 14, 12, 0.4, 2.6, (174, 214, 241), 3)
    cv.arc(cx - 12, cy + 14, 9, 3.4, 5.8, (174, 214, 241), 3)


def draw_flag(cv, x, y, kind):
    """One small flag tile, 84x56, top-left at (x, y)."""
    if kind == "china":
        cv.fill_rect(x, y, 84, 56, (222, 41, 16))
        cv.fill_poly(star_points(x + 20, y + 16, 10, 4), (255, 222, 0))
        for dx, dy in ((36, 8), (40, 20), (36, 32), (30, 40)):
            cv.fill_circle(x + dx, y + dy, 3, (255, 222, 0))
    elif kind == "usa":
        for i in range(7):
            cv.fill_rect(x, y + i * 8, 84, 4 if i % 2 == 0 else 8,
                         (178, 34, 52) if i % 2 == 0 else (240, 240, 240))
        cv.fill_rect(x, y, 38, 30, (60, 59, 110))
        for r in range(3):
            for c in range(4):
                cv.fill_circle(x + 6 + c * 9, y + 6 + r * 9, 2, (240, 240, 240))
    else:  # russia
        cv.fill_rect(x, y, 84, 19, (240, 240, 240))
        cv.fill_rect(x, y + 19, 84, 19, (0, 57, 166))
        cv.fill_rect(x, y + 38, 84, 18, (213, 43, 30))
        cv.rect_outline(x, y, 84, 56, (120, 120, 120), 1)


def icon_satellite(cv, cx, cy, color):
    cv.fill_rect(cx - 8, cy - 10, 16, 20, color)
    cv.fill_rect(cx - 40, cy - 7, 26, 14, color)
    cv.fill_rect(cx + 14, cy - 7, 26, 14, color)
    cv.line(cx - 27, cy - 7, cx - 27, cy + 7, INK, 2)
    cv.line(cx + 27, cy - 7, cx + 27, cy + 7, INK, 2)
    cv.arc(cx + 4, cy + 16, 9, 1.9, 4.2, color, 3)
    cv.arc(cx + 4, cy + 16, 17, 1.9, 4.2, color, 3)


# ---------------------------------------------------------------------------
# The page.
# ---------------------------------------------------------------------------
def story_card(cv, x, y, w, h, strip, icon, headline, sub):
    cv.fill_rect(x, y, w, h, CARD)
    cv.rect_outline(x, y, w, h, INK, 2)
    cv.fill_rect(x, y, w, 8, strip)
    icon(cv, x + 58, y + h // 2 + 6)
    tx = x + 116
    ty = y + 28
    for line in headline:
        cv.text(tx, ty, line, 4, INK)
        ty += 35
    ty += 2
    for line in sub:
        cv.text(tx, ty, line, 3, GREY)
        ty += 26


def compose():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.text_centered(W // 2, 32, "THE WORLD IN ONE IMAGE", 4, INK)
    cv.fill_rect(36, 74, 952, 4, RED)
    cv.fill_rect(36, 83, 952, 1, RED)
    cv.text_centered(W // 2, 96, "FRIDAY", 6, INK)
    cv.text_centered(W // 2, 150, "20 NOVEMBER 2026", 9, INK)
    cv.fill_rect(36, 224, 952, 2, INK)

    # Lead story: the Shenzhen trilateral summit.
    ly, lh = 236, 178
    cv.fill_rect(36, ly, 952, lh, NAVY)
    cv.fill_rect(36, ly, 952, 6, GOLD)
    fx = 64
    for kind in ("usa", "china", "russia"):
        cv.line(fx + 4, ly + 44, fx + 4, ly + 148, (150, 158, 175), 3)
        draw_flag(cv, fx, ly + 48, kind)
        fx += 100
    cv.text(392, ly + 30, "TRUMP, XI AND PUTIN", 5, WHITE)
    cv.text(392, ly + 78, "ISSUE PEACE PLEDGE", 5, WHITE)
    cv.text(392, ly + 128, "TRILATERAL SUMMIT IN SHENZHEN", 3,
            (190, 198, 214))

    # Story grid: two columns, three rows.
    cards = [
        ((176, 58, 46), icon_drone,
         ["RUSSIA FIRES", "400+ DRONES,", "110 MISSILES"],
         ["TWO FALL IN POLAND"]),
        ((108, 52, 131), icon_scales,
         ["MYANMAR GUILTY", "OF GENOCIDE"],
         ["UN COURT RULES ON", "ROHINGYA CASE"]),
        ((33, 47, 61), icon_chart,
         ["NASDAQ DIVES", "5.3% - AI ROUT"],
         ["NVIDIA -14%", "BTC UNDER $56K"]),
        ((26, 82, 118), icon_ship,
         ["TANKERS STRUCK", "BY SEA MINES"],
         ["STRAIT OF HORMUZ", "US BLOCKADE HOLDS"]),
        ((30, 132, 73), icon_leaf,
         ["CLIMATE TALKS", "STALL AT COP31"],
         ["DEADLOCK OVER", "FOSSIL FUELS"]),
        ((183, 149, 11), icon_frame,
         ["VAN GOGH SETS", "$190M RECORD"],
         ["PAINTING FETCHES", "$190.4M"]),
    ]
    cw, chh, gx, gy = 470, 165, 12, 8
    top = 426
    for i, (strip, icon, headline, sub) in enumerate(cards):
        x = 36 + (i % 2) * (cw + gx)
        y = top + (i // 2) * (chh + gy)
        story_card(cv, x, y, cw, chh, strip, icon, headline, sub)

    # Footer band: the science one-liner.
    fy = 949
    cv.fill_rect(36, fy, 952, 51, RED)
    icon_satellite(cv, 92, fy + 25, WHITE)
    cv.text(140, fy + 15, "VOYAGER 1 CALLS HOME - ONE LIGHT-DAY AWAY", 3, WHITE)

    return cv


# ---------------------------------------------------------------------------
# PNG writer (zlib + chunk framing, no external dependencies).
# ---------------------------------------------------------------------------
def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * stride:(yy + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(compose())
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
