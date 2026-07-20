def main():
    app = Application.builder().token(config.BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rank", rank_command))
    app.add_handler(CommandHandler("topchatters", topchatters_command))
    app.add_handler(CommandHandler("rankings", rankings_command))
    app.add_handler(CallbackQueryHandler(rankings_callback, pattern="^rank_"))

    app.add_handler(CommandHandler("stats", stats_command))
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_command)],
        states={BROADCAST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_receive)]},
        fallbacks=[]
    )
    app.add_handler(broadcast_conv)

    # Message counter (must be last to avoid catching commands)
    app.add_handler(MessageHandler(filters.ALL, message_counter))

    app.run_polling()
