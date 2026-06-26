import os
from PIL import Image, ImageDraw, ImageFont
from app.settings import CUSTOM_ICON_PATH


def make_icon(alert=False):
    size       = 140
    emoji_size = 80

    if os.path.exists(CUSTOM_ICON_PATH):
        try:
            base = Image.open(CUSTOM_ICON_PATH).convert("RGBA").resize((size, size), Image.LANCZOS)
        except Exception:
            base = _default_icon(size)
    else:
        base = _default_icon(size)

    if alert:
        try:
            emoji_img = Image.new("RGBA", (emoji_size, emoji_size), (0, 0, 0, 0))
            draw_e    = ImageDraw.Draw(emoji_img)
            fnt_emoji = ImageFont.truetype("seguiemj.ttf", emoji_size - 5)
            draw_e.text((0, 0), "⚠️", font=fnt_emoji, embedded_color=True)
            base.paste(emoji_img, (size - emoji_size, 0), emoji_img)
        except Exception:
            draw = ImageDraw.Draw(base)
            draw.ellipse([95, 0, 140, 45], fill="#ff0000", outline="white", width=2)

    return base


def _default_icon(size=140):
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill="#1e40af")
    try:
        fnt = ImageFont.truetype("arialbd.ttf", 48)
    except Exception:
        fnt = ImageFont.load_default()
    draw.text((30, 30), "R", fill="white", font=fnt)
    return img
