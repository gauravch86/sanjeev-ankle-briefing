#!/usr/bin/env python3
"""Rebuild MRI teaching annotations + phone-first cards (safe margins, bilingual)."""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path("/workspace/health/sanjeev-ankle")
MEDIA = ROOT / "media"

FONT_EN = "/usr/share/fonts/truetype/sand-box/google/Mukta/Mukta-ExtraBold.ttf"
FONT_HI = "/usr/share/fonts/truetype/sand-box/google/Mukta/Mukta-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/sand-box/google/Mukta/Mukta-SemiBold.ttf"
FONT_FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

YELLOW = (255, 214, 64)
YELLOW_DIM = (255, 214, 64, 200)
RED = (255, 90, 110)
RED_SOFT = (255, 90, 110, 110)
WHITE = (255, 255, 255)
BANNER_BG = (8, 14, 28, 230)
PILL_A_BG = (20, 28, 18, 235)
PILL_B_BG = (36, 16, 22, 235)
DARK = (0, 0, 0, 200)


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    for p in (path, FONT_FALLBACK, FONT_EN):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def rounded_rect(draw, xy, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_banner(base: Image.Image, top_text: str, bottom_pills: list[tuple[str, str, tuple, tuple]]):
    """Draw top title bar + bottom pill row. All text ≥8% from edges."""
    w, h = base.size
    margin = max(int(w * 0.08), 56)
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    top_h = max(72, int(h * 0.07))
    bot_h = max(150, int(h * 0.14))
    d.rectangle([0, 0, w, top_h], fill=BANNER_BG)
    d.rectangle([0, h - bot_h, w, h], fill=BANNER_BG)

    f_top = font(FONT_EN, 28 if w >= 1200 else 22)
    tw, th = text_size(d, top_text, f_top)
    d.text(((w - tw) // 2, (top_h - th) // 2 - 2), top_text, font=f_top, fill=YELLOW)

    # Bottom pills: two large callouts
    gap = 16
    usable = w - 2 * margin
    pill_w = (usable - gap) // 2
    pill_h = bot_h - 36
    y0 = h - bot_h + 18
    for i, (title, subtitle, border, bg) in enumerate(bottom_pills):
        x0 = margin + i * (pill_w + gap)
        rounded_rect(d, [x0, y0, x0 + pill_w, y0 + pill_h], 18, bg, border, 3)
        f_t = font(FONT_EN, 36 if w >= 1200 else 28)
        f_s = font(FONT_HI, 24 if w >= 1200 else 20)
        # title
        tt_w, tt_h = text_size(d, title, f_t)
        d.text((x0 + 18, y0 + 14), title, font=f_t, fill=WHITE)
        # subtitle (may be Hindi + English)
        d.text((x0 + 18, y0 + 14 + tt_h + 4), subtitle, font=f_s, fill=border)

    out = Image.alpha_composite(base.convert("RGBA"), overlay)
    return out.convert("RGB")


def annotate_film1(src_path: Path, out_path: Path):
    """Sagittal sheet: yellow ovals on cyst, red bars on subtalar; labels in bottom pills."""
    im = Image.open(src_path).convert("RGB")
    # Normalize to 1400 canvas like prior web assets
    im = im.resize((1400, 1400), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # Approximate slice markers (from prior annotation clusters / anatomy)
    # Yellow cyst ovals (talus bright pockets) — mid grid
    cyst_ovals = [
        (310, 700, 390, 760),
        (520, 690, 600, 750),
        (310, 870, 400, 940),
        (520, 860, 610, 930),
        (730, 700, 810, 760),
    ]
    for box in cyst_ovals:
        d.ellipse(box, outline=YELLOW + (255,), width=4)
    # Subtle yellow fill
    for box in cyst_ovals[:3]:
        d.ellipse(box, outline=None, fill=(255, 214, 64, 35))

    # Arrow toward a clear cyst
    d.line([(250, 650), (330, 720)], fill=YELLOW + (255,), width=4)
    # arrow head
    d.polygon([(330, 720), (310, 708), (318, 738)], fill=YELLOW + (255,))

    # Red subtalar bars
    bars = [
        (280, 760, 420, 790),
        (490, 750, 630, 780),
        (280, 940, 420, 970),
        (490, 930, 630, 960),
        (700, 755, 840, 785),
    ]
    for box in bars:
        d.rectangle(box, fill=RED_SOFT, outline=RED + (220,), width=2)

    composed = Image.alpha_composite(im.convert("RGBA"), overlay)
    pills = [
        (
            "A — Talus cyst",
            "हड्डी में सिस्ट · bright pocket in talus",
            YELLOW,
            PILL_A_BG,
        ),
        (
            "B — Subtalar joint",
            "सबटेलर जोड़ · main problem area",
            RED,
            PILL_B_BG,
        ),
    ]
    final = draw_banner(
        composed,
        "Teaching labels on hospital MRI (sagittal) — family discussion only",
        pills,
    )
    # Footer legend strip already in banner; add tiny center note
    d2 = ImageDraw.Draw(final)
    f_note = font(FONT_REG, 18)
    note = "Yellow = cyst · Red = subtalar irritation/fluid · Educational — not a new diagnosis"
    nw, nh = text_size(d2, note, f_note)
    # place just above bottom pills area top edge (~14% from bottom already banner)
    # Actually inside bottom banner above pills - skip if crowded; put under top banner
    d2.text(((1400 - nw) // 2, 78), note, font=f_note, fill=(180, 200, 230))

    final.save(out_path, quality=88, optimize=True)
    print("wrote", out_path, final.size)


def annotate_film3(src_path: Path, out_path: Path):
    im = Image.open(src_path).convert("RGB").resize((1400, 1400), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # Axial sheet — cyst often bright mid-right; subtalar lower row
    cyst_ovals = [
        (860, 700, 960, 800),
        (1040, 690, 1140, 790),
        (860, 860, 960, 960),
        (1040, 850, 1140, 950),
        (680, 710, 770, 800),
    ]
    for box in cyst_ovals:
        d.ellipse(box, outline=YELLOW + (255,), width=4)
    d.line([(780, 650), (880, 730)], fill=YELLOW + (255,), width=4)
    d.polygon([(880, 730), (858, 718), (868, 748)], fill=YELLOW + (255,))

    bars = [
        (640, 980, 780, 1020),
        (820, 975, 960, 1015),
        (1000, 970, 1140, 1010),
    ]
    for box in bars:
        d.rectangle(box, fill=RED_SOFT, outline=RED + (220,), width=2)

    composed = Image.alpha_composite(im.convert("RGBA"), overlay)
    pills = [
        (
            "A — Talus cyst",
            "हड्डी में सिस्ट · bright focus",
            YELLOW,
            PILL_A_BG,
        ),
        (
            "B — Subtalar joint",
            "सबटेलर जोड़ · irritation / fluid",
            RED,
            PILL_B_BG,
        ),
    ]
    final = draw_banner(
        composed,
        "Teaching labels on hospital MRI (axial) — family discussion only",
        pills,
    )
    d2 = ImageDraw.Draw(final)
    f_note = font(FONT_REG, 18)
    note = "Yellow = cyst · Red = subtalar irritation/fluid · Educational — not a new diagnosis"
    nw, _ = text_size(d2, note, f_note)
    d2.text(((1400 - nw) // 2, 78), note, font=f_note, fill=(180, 200, 230))
    final.save(out_path, quality=88, optimize=True)
    print("wrote", out_path, final.size)


def phone_card(
    crop: Image.Image,
    out_path: Path,
    title: str,
    body_lines: list[str],
    footer: str,
    accent: tuple,
    mark: str,
):
    """Phone-first teaching card ~1080 wide with large in-frame text."""
    # Target width 1080, keep aspect, add text panels
    target_w = 1080
    # Build canvas: image on top 55%, text panels stacked
    crop = crop.convert("RGB")
    # Resize crop to width 1080
    scale = target_w / crop.width
    img_h = int(crop.height * scale)
    crop_r = crop.resize((target_w, img_h), Image.Resampling.LANCZOS)

    # Extra vertical space for text
    panel_h = 420
    canvas = Image.new("RGB", (target_w, img_h + panel_h), (10, 16, 30))
    canvas.paste(crop_r, (0, 0))

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # Semi-opaque gradient bar over bottom of image for title readability
    bar_top = max(0, img_h - 120)
    for y in range(bar_top, img_h):
        a = int(180 * (y - bar_top) / max(1, img_h - bar_top))
        d.rectangle([0, y, target_w, y + 1], fill=(0, 0, 0, a))

    # Draw mark on image
    if mark == "cyst":
        # oval near center of crop
        cx, cy = target_w // 2, int(img_h * 0.42)
        box = (cx - 90, cy - 70, cx + 90, cy + 70)
        d.ellipse(box, outline=accent + (255,), width=6)
        d.ellipse(box, fill=accent + (40,))
        # arrow
        d.line([(cx - 180, cy - 140), (cx - 70, cy - 40)], fill=accent + (255,), width=6)
        d.polygon(
            [(cx - 70, cy - 40), (cx - 110, cy - 55), (cx - 95, cy - 20)],
            fill=accent + (255,),
        )
    elif mark == "subtalar":
        cy = int(img_h * 0.55)
        d.rectangle(
            [int(target_w * 0.18), cy - 18, int(target_w * 0.82), cy + 22],
            fill=accent + (90,),
            outline=accent + (255,),
            width=4,
        )
        d.line([(int(target_w * 0.82) + 10, cy), (int(target_w * 0.92), cy + 80)], fill=accent + (255,), width=5)

    # Title on image bottom
    f_title = font(FONT_EN, 48)
    # wrap title if needed
    d.text((36, img_h - 100), title, font=f_title, fill=accent + (255,))

    # Body panel
    d.rectangle([0, img_h, target_w, img_h + panel_h], fill=(12, 20, 36, 255))
    f_body = font(FONT_REG, 32)
    f_foot = font(FONT_REG, 24)
    y = img_h + 28
    for line in body_lines:
        # simple wrap
        words = line.split()
        cur = ""
        for word in words:
            trial = (cur + " " + word).strip()
            tw, th = text_size(d, trial, f_body)
            if tw > target_w - 72:
                d.text((36, y), cur, font=f_body, fill=WHITE)
                y += th + 8
                cur = word
            else:
                cur = trial
        if cur:
            tw, th = text_size(d, cur, f_body)
            d.text((36, y), cur, font=f_body, fill=WHITE)
            y += th + 14

    # Footer box
    rounded_rect(
        d,
        [24, img_h + panel_h - 90, target_w - 24, img_h + panel_h - 24],
        14,
        (0, 0, 0, 180),
        accent,
        2,
    )
    fw, fh = text_size(d, footer, f_foot)
    d.text((40, img_h + panel_h - 90 + (66 - fh) // 2), footer, font=f_foot, fill=(220, 230, 245))

    out = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    out.save(out_path, quality=90, optimize=True)
    print("wrote", out_path, out.size)


def combined_card(cyst_crop: Image.Image, sub_crop: Image.Image, out_path: Path):
    target_w = 1080
    # Two panels stacked
    def prep(im, hmax=520):
        im = im.convert("RGB")
        scale = target_w / im.width
        r = im.resize((target_w, int(im.height * scale)), Image.Resampling.LANCZOS)
        if r.height > hmax:
            top = (r.height - hmax) // 2
            r = r.crop((0, top, target_w, top + hmax))
        return r

    a = prep(cyst_crop)
    b = prep(sub_crop)
    header_h = 100
    gap = 16
    footer_h = 80
    total_h = header_h + a.height + gap + b.height + footer_h + 200
    canvas = Image.new("RGB", (target_w, total_h), (10, 16, 30))
    d0 = ImageDraw.Draw(canvas)
    f_h = font(FONT_EN, 40)
    title = "A + B — Two MRI teaching labels"
    tw, th = text_size(d0, title, f_h)
    d0.text(((target_w - tw) // 2, (header_h - th) // 2), title, font=f_h, fill=YELLOW)

    y = header_h
    canvas.paste(a, (0, y))
    # labels strip under each
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # cyst mark
    d.ellipse([target_w // 2 - 80, y + a.height // 2 - 60, target_w // 2 + 80, y + a.height // 2 + 50],
              outline=YELLOW + (255,), width=5)

    y2 = y + a.height + gap
    canvas.paste(b, (0, y2))
    d.rectangle(
        [int(target_w * 0.2), y2 + int(b.height * 0.55), int(target_w * 0.8), y2 + int(b.height * 0.55) + 36],
        fill=RED + (100,),
        outline=RED + (255,),
        width=3,
    )

    # text panels
    text_y = y2 + b.height + 20
    f_t = font(FONT_EN, 34)
    f_b = font(FONT_REG, 28)
    lines = [
        ("A — Talus cyst / हड्डी में सिस्ट", YELLOW),
        ("Bright pocket inside talus (~13×11 mm & 16×10 mm).", WHITE),
        ("B — Subtalar joint / सबटेलर जोड़", RED),
        ("Joint under talus — MRI irritation/fluid; main discussion focus.", WHITE),
    ]
    yy = text_y
    for text, col in lines:
        d.text((32, yy), text, font=f_t if text.startswith(("A", "B")) else f_b, fill=col if isinstance(col, tuple) and len(col) == 3 else col)
        yy += 42

    foot = "Educational labels on hospital MRI — not a new diagnosis"
    f_f = font(FONT_REG, 24)
    rounded_rect(d, [24, total_h - 70, target_w - 24, total_h - 20], 12, (0, 0, 0, 180), (120, 160, 220), 2)
    d.text((40, total_h - 58), foot, font=f_f, fill=(220, 230, 245))

    out = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    out.save(out_path, quality=90, optimize=True)
    print("wrote", out_path, out.size)


def make_closeups(film1_ann: Path):
    """Rebuild closeups from annotated sheet WITHOUT right-edge text (markers only region)."""
    im = Image.open(film1_ann).convert("RGB")
    # Crop central teaching region (away from any edge labels — labels now in bottom banner)
    cyst = im.crop((140, 560, 1040, 1120)).resize((900, 560), Image.Resampling.LANCZOS)
    # Add in-frame caption bars so crop alone is readable
    for img, path, title, accent in [
        (cyst, MEDIA / "web-cyst-closeup.jpg", "A — Talus cyst / हड्डी में सिस्ट", YELLOW),
        (im.crop((160, 600, 1060, 1140)).resize((900, 540), Image.Resampling.LANCZOS),
         MEDIA / "web-subtalar-closeup.jpg", "B — Subtalar / सबटेलर जोड़", RED),
    ]:
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        d.rectangle([0, img.height - 70, img.width, img.height], fill=(0, 0, 0, 200))
        f = font(FONT_EN, 28)
        d.text((16, img.height - 52), title, font=f, fill=accent)
        out = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        out.save(path, quality=88, optimize=True)
        print("wrote", path, out.size)


def main():
    src1 = MEDIA / "web-mri-film-1.jpg"
    src3 = MEDIA / "web-mri-film-3.jpg"
    if not src1.exists():
        src1 = MEDIA / "mri-film-1.jpg"
    if not src3.exists():
        src3 = MEDIA / "mri-film-3.jpg"

    ann1 = MEDIA / "web-mri-film-1-annotated.jpg"
    ann3 = MEDIA / "web-mri-film-3-annotated.jpg"
    annotate_film1(src1, ann1)
    annotate_film3(src3, ann3)

    # Phone crops from clean source — clearest sagittal mid-grid slices
    src = Image.open(src1).convert("RGB")
    if src.size != (1400, 1400):
        src = src.resize((1400, 1400), Image.Resampling.LANCZOS)

    # ~2 sagittal slices showing talus cyst / subtalar (left-center grid)
    cyst_crop = src.crop((160, 580, 700, 1080))
    sub_crop = src.crop((200, 620, 760, 1100))

    phone_card(
        cyst_crop,
        MEDIA / "teach-cyst-phone.jpg",
        "A — Talus cyst / हड्डी में सिस्ट",
        [
            "Bright pocket inside the ankle bone (talus).",
            "Report size about 13×11 mm and 16×10 mm.",
            "Yellow oval = educational mark on hospital MRI.",
        ],
        "Educational label on hospital MRI — not a new diagnosis",
        YELLOW,
        "cyst",
    )
    phone_card(
        sub_crop,
        MEDIA / "teach-subtalar-phone.jpg",
        "B — Subtalar joint / सबटेलर जोड़",
        [
            "Joint under the ankle bone where MRI shows irritation / fluid.",
            "This is the main problem area doctors discuss.",
            "Red bar = educational mark on hospital MRI.",
        ],
        "Educational label on hospital MRI — not a new diagnosis",
        RED,
        "subtalar",
    )
    combined_card(cyst_crop, sub_crop, MEDIA / "teach-both-phone.jpg")
    # legend alias
    combined = MEDIA / "teach-both-phone.jpg"
    legend = MEDIA / "teach-legend-phone.jpg"
    Image.open(combined).save(legend, quality=90, optimize=True)
    print("wrote", legend)

    make_closeups(ann1)

    # cleanup debug
    for p in MEDIA.glob("_debug*.jpg"):
        p.unlink()
        print("removed", p)


if __name__ == "__main__":
    main()
