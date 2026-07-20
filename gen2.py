async def generate_top3_card(bot, chat_id, date_str):
    # Fetch top 3 users for today (or use overall? The spec says "today's msg count")
    top3 = await db.get_top_users(chat_id, mode="daily", limit=3)
    # Ensure we have 3, fill with placeholders if missing

    # Create background: dark with warm orange/amber gradient
    width, height = 1920, 1080
    im = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(im)
    for y in range(height):
        r = int(20 + (60 - 20) * (y / height))
        g = int(10 + (30 - 10) * (y / height))
        b = int(5 + (10 - 5) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add vignette
    # ...

    # Header
    header_h = 200
    header_y = 60
    # Draw a rounded rectangle header with glowing outline
    # ...

    # Podium layout
    # Positions: 2nd left (x=width*0.25), 1st center (x=width*0.5), 3rd right (x=width*0.75)
    # 1st is larger
    # ...

    # For each rank, draw avatar, username, count, rank number.
    # Use accent colors: gold, silver, bronze.

    # This is a large piece – we'll provide the full implementation in the final code repository.

    # Return BytesIO
    return buf
