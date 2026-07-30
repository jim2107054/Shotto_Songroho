"""
Server-side shareable verdict card rendering.
"""

from io import BytesIO
from typing import Any, Dict, List

import qrcode
from PIL import Image, ImageDraw, ImageFont

CARD_W = 1200
CARD_H = 630
COLORS = {
    "verified": "#198754",
    "disputed": "#FE9F43",
    "false": "#DC3545",
    "unverifiable": "#646B72",
}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/Nunito-Bold.ttf" if bold else "C:/Windows/Fonts/Nunito-Regular.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1].rstrip(".") + "..."
    return lines


def render_verdict_card(verdict: str, confidence: float, summary: str, sources: List[Dict[str, Any]]) -> bytes:
    accent = COLORS.get(verdict, COLORS["unverifiable"])
    image = Image.new("RGB", (CARD_W, CARD_H), "#F9FAFB")
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((40, 40, CARD_W - 40, CARD_H - 40), radius=16, fill="#FFFFFF", outline="#E6EAED", width=2)
    draw.rectangle((40, 40, 64, CARD_H - 40), fill=accent)

    draw.text((96, 82), "Shotto Songroho", fill="#092C4C", font=_font(36, True))
    draw.text((96, 128), "Evidence-backed July Revolution verdict", fill="#646B72", font=_font(22))

    badge = verdict.upper()
    draw.rounded_rectangle((96, 190, 96 + 28 * len(badge), 250), radius=12, fill=accent)
    draw.text((116, 205), badge, fill="#FFFFFF", font=_font(28, True))
    draw.text((96, 278), f"Confidence: {round(confidence * 100)}%", fill="#212B36", font=_font(28, True))

    body_font = _font(28)
    for index, line in enumerate(_wrap(draw, summary or "No summary available.", body_font, 720, 5)):
        draw.text((96, 338 + index * 40), line, fill="#212B36", font=body_font)

    source_url = ""
    source_label = "No source URL"
    if sources:
        first = sources[0]
        source_url = first.get("url") or ""
        source_label = first.get("source_org") or first.get("title") or source_url or source_label

    qr_payload = source_url or "https://shotto-songroho.local/sources"
    qr = qrcode.QRCode(border=1, box_size=8)
    qr.add_data(qr_payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#092C4C", back_color="#FFFFFF").convert("RGB").resize((220, 220))
    image.paste(qr_img, (880, 238))
    draw.text((880, 480), "Source QR", fill="#092C4C", font=_font(22, True))
    for index, line in enumerate(_wrap(draw, source_label, _font(18), 240, 2)):
        draw.text((880, 512 + index * 26), line, fill="#646B72", font=_font(18))

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
