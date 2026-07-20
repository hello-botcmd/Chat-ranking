from telegram import Bot
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import io
import os
import asyncio
from datetime import datetime

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"   # Adjust for your system
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


async def get_user_avatar(bot: Bot, user_id):
    photos = await bot.get_user_profile_photos(user_id, limit=1)
    if photos.total_count == 0:
        return None
    file = await bot.get_file(photos.photos[0][-1].file_id)
    # Download image
    async with aiohttp.ClientSession() as session:
        resp = await session.get(file.file_path)
        img_data = await resp.read()
    return Image.open(io.BytesIO(img_data))


def round_corners(im, rad):
    # Create rounded rectangle mask
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    mask = Image.new('L', im.size, 0)
    mask.paste(circle, (0, 0))
    mask.paste(circle, (im.width - rad * 2, 0))
    mask.paste(circle, (0, im.height - rad * 2))
    mask.paste(circle, (im.width - rad * 2, im.height - rad * 2))
    im.putalpha(mask)
    return im
