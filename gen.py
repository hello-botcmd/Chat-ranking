async def generate_rank_card(bot, user_id, chat_id):
    # Fetch user data
    user = await bot.get_chat(user_id)
    first = user.first_name or ""
    last = user.last_name or ""
    full_name = f"{first} {last}".strip()
    username = user.username or first

    # Get stats
    rank, total = await db.get_user_rank(chat_id, user_id, "total")
    daily_rank, daily_count = await db.get_user_rank(chat_id, user_id, "daily")
    weekly_rank, weekly_count = await db.get_user_rank(chat_id, user_id, "weekly")

    # We need today's count and total count. The `get_user_rank` returns rank and count.
    # For today and total, we already have them.
    # However, we also need the rank number for the card.
    # We'll use the total rank for the rank card.
    # Today count: daily_count, Total count: total.
    # But we also need the user's rank (position) – we have it.
    # For the rank card, we display the total rank.
    rank_value = rank if rank else "?"

    # Create base image
    width, height = 1920, 1080
    im = Image.new('RGB', (width, height), color=(10, 20, 40))
    draw = ImageDraw.Draw(im)

    # 1. Gradient background (top‑to‑bottom)
    for y in range(height):
        r = int(10 + (20 - 10) * (y / height))
        g = int(20 + (80 - 20) * (y / height))
        b = int(40 + (120 - 40) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 2. Geometric polygons (semi‑transparent)
    # We'll draw some random triangles and hexagons using a predefined set.
    # For simplicity, we'll use a static pattern – can be improved.
    import random
    random.seed(42)  # reproducible
    for _ in range(30):
        points = []
        for _ in range(3):
            x = random.randint(0, width)
            y = random.randint(0, height)
            points.append((x, y))
        alpha = random.randint(30, 80)
        color = (100, 150, 255, alpha)
        draw.polygon(points, fill=color, outline=None)

    # 3. Glassmorphism card (main content)
    card_margin = 60
    card_radius = 30
    card_rect = [card_margin, card_margin, width - card_margin, height - card_margin]
    # Create a semi‑transparent black overlay, then blur it
    card_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_img)
    card_draw.rounded_rectangle(card_rect, radius=card_radius, fill=(255, 255, 255, 30))
    # Apply Gaussian blur
    card_img = card_img.filter(ImageFilter.GaussianBlur(radius=5))
    im = Image.alpha_composite(im.convert('RGBA'), card_img).convert('RGB')

    # Redraw the card outline (glossy border)
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle(card_rect, radius=card_radius, outline=(200, 230, 255, 100), width=2)

    # 4. Avatar (top‑left)
    avatar_size = 200
    avatar_x = card_margin + 40
    avatar_y = card_margin + 40
    avatar = await get_user_avatar(bot, user_id)
    if avatar:
        avatar = avatar.resize((avatar_size, avatar_size), Image.LANCZOS)
        # Make it circular (or rounded square)
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        avatar = ImageOps.fit(avatar, (avatar_size, avatar_size), centering=(0.5, 0.5))
        avatar.putalpha(mask)
        im.paste(avatar, (avatar_x, avatar_y), avatar)
    else:
        # Placeholder circle
        draw.ellipse((avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size),
                     fill=(100, 150, 200), outline=(200, 230, 255))

    # 5. Real name and username
    # Real name above username
    font_name = ImageFont.truetype(FONT_BOLD, 60)
    font_user = ImageFont.truetype(FONT_BOLD, 48)

    text_x = avatar_x + avatar_size + 40
    text_y = avatar_y + 10
    # Real name (bright white)
    draw.text((text_x, text_y), full_name, fill=(255, 255, 255), font=font_name)
    # Username (bright cyan)
    username_text = f"@{username}" if username.startswith('@') else f"@{username}"
    draw.text((text_x, text_y + 80), username_text, fill=(0, 255, 255), font=font_user)

    # 6. Three stat cards at bottom
    card_w = 400
    card_h = 150
    spacing = 60
    total_width = 3 * card_w + 2 * spacing
    start_x = (width - total_width) // 2
    bottom_y = height - card_margin - 100

    # Define icons and labels
    stats = [
        ("🏆", "Rank", f"#{rank_value}"),
        ("💬", "Today", str(daily_count)),
        ("🌐", "Total", str(total))
    ]

    for i, (icon, label, value) in enumerate(stats):
        x = start_x + i * (card_w + spacing)
        y = bottom_y

        # Glossy card
        card_rect = [x, y, x + card_w, y + card_h]
        # Draw rounded rect with gradient
        card_img = Image.new('RGBA', (card_w, card_h), (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_img)
        card_draw.rounded_rectangle([0, 0, card_w, card_h], radius=20, fill=(30, 60, 120, 200))
        # Glossy highlight
        highlight = Image.new('RGBA', (card_w, card_h), (0, 0, 0, 0))
        h_draw = ImageDraw.Draw(highlight)
        h_draw.rounded_rectangle([0, 0, card_w, card_h//2], radius=20, fill=(255, 255, 255, 30))
        card_img = Image.alpha_composite(card_img, highlight)
        # Paste onto main
        im.paste(card_img, (x, y), card_img)

        # Draw icon and text on main image
        draw = ImageDraw.Draw(im)
        # Icon
        font_icon = ImageFont.truetype(FONT_PATH, 60)
        draw.text((x + 20, y + 20), icon, fill=(255, 255, 255), font=font_icon)
        # Label
        font_label = ImageFont.truetype(FONT_BOLD, 30)
        draw.text((x + 80, y + 25), label, fill=(200, 220, 255), font=font_label)
        # Value
        font_value = ImageFont.truetype(FONT_BOLD, 50)
        draw.text((x + 80, y + 70), value, fill=(255, 255, 255), font=font_value)

    # Save to BytesIO
    buf = io.BytesIO()
    im.save(buf, format='PNG')
    buf.seek(0)
    return buf
