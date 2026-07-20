from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
import config
import db
import image_gen
import io

# States for broadcast conversation
BROADCAST_TEXT = 0


async def start(update: Update, context):
    user = update.effective_user
    await db.ensure_user(user.id, user.username, user.first_name, user.last_name or "")
    # Send welcome image
    with open(config.WELCOME_IMAGE_PATH, 'rb') as f:
        await update.message.reply_photo(
            photo=f,
            caption="Welcome! I'm a ranking bot. Add me to your group and start tracking messages!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Add me in your group",
                                      url=f"https://t.me/{config.BOT_USERNAME}?startgroup=start")]
            ])
        )


async def rank_command(update: Update, context):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command works only in groups.")
        return
    user = update.effective_user
    # Generate image
    img_buf = await image_gen.generate_rank_card(context.bot, user.id, chat.id)
    await update.message.reply_photo(photo=img_buf, filename="rank.png")


async def topchatters_command(update: Update, context):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command works only in groups.")
        return
    img_buf = await image_gen.generate_top3_card(context.bot, chat.id)
    await update.message.reply_photo(photo=img_buf, filename="top3.png")


async def rankings_command(update: Update, context):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command works only in groups.")
        return
    # Send message with buttons
    keyboard = [
        [InlineKeyboardButton("Overall", callback_data="rank_overall"),
         InlineKeyboardButton("Daily", callback_data="rank_daily"),
         InlineKeyboardButton("Weekly", callback_data="rank_weekly")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Show initial top10 (overall)
    top10 = await db.get_top_users(chat.id, "total", 10)
    text = format_top10(top10, "Overall")
    await update.message.reply_text(text, reply_markup=reply_markup)


def format_top10(top10, mode_name):
    if not top10:
        return f"📊 Top 10 {mode_name}:\nNo data yet."
    lines = [f"📊 Top 10 {mode_name}:"]
    for i, (uid, count) in enumerate(top10, 1):
        # We need username, but we can store in DB or fetch from user cache.
        # For simplicity, we'll fetch from context.bot.get_chat (maybe async)
        # But to avoid blocking, we can cache usernames in DB.
        # We'll implement a cache later.
        lines.append(f"{i}. User {uid} – {count} msgs")
    return "\n".join(lines)


async def rankings_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    mode = query.data.split("_")[1]  # overall, daily, weekly
    chat = update.effective_chat
    top10 = await db.get_top_users(chat.id, mode, 10)
    mode_name = {"overall": "Overall", "daily": "Daily", "weekly": "Weekly"}[mode]
    text = format_top10(top10, mode_name)
    await query.edit_message_text(text, reply_markup=query.message.reply_markup)


# Owner commands
async def stats_command(update: Update, context):
    if update.effective_user.id != config.OWNER_ID:
        await update.message.reply_text("Unauthorized.")
        return
    total_users = await db.get_total_users_count()
    total_chats = await db.get_total_chats_count()
    await update.message.reply_text(f"📊 Bot Stats:\nTotal Users: {total_users}\nTotal Groups: {total_chats}")


async def broadcast_command(update: Update, context):
    if update.effective_user.id != config.OWNER_ID:
        await update.message.reply_text("Unauthorized.")
        return
    await update.message.reply_text("Please send the message you want to broadcast to all users.")
    return BROADCAST_TEXT


async def broadcast_receive(update: Update, context):
    if update.effective_user.id != config.OWNER_ID:
        return ConversationHandler.END
    text = update.message.text
    users = await db.get_all_users()
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            sent += 1
            await asyncio.sleep(0.05)  # avoid flood
        except:
            pass
    await update.message.reply_text(f"Broadcast sent to {sent} users.")
    return ConversationHandler.END


async def message_counter(update: Update, context):
    # Count all messages in groups
    if update.effective_chat.type in ["group", "supergroup"]:
        chat = update.effective_chat
        user = update.effective_user
        if user.is_bot:
            return
        # Ensure chat and user in DB
        await db.ensure_chat(chat.id, chat.title or "Unnamed")
        await db.ensure_user(user.id, user.username, user.first_name, user.last_name or "")
        # Increment stats
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        await db.increment_stats(chat.id, user.id, today_str)
