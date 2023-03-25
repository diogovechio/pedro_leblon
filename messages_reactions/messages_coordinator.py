    if incoming.message is not None:
        message = incoming.message

        from_samuel = message.from_.is_premium
        from_debug_chats = message.chat.id in (-20341310, 8375482)

        if message.chat.id in bot.allowed_list:
            if str(message.from_.id) not in bot.config.ignore_users or message.from_.username not in bot.config.ignore_users:
                if message.photo and message.chat.id not in bot.config.not_internal_chats:
                    bot.loop.create_task(
                        image_reactions(
                            bot=bot,
                            message=message,
                            method='cropper' if from_samuel or from_debug_chats else 'face_classifier',
                            always_send_crop=from_debug_chats
                        )
                    )

                if message.text or message.caption:
                    message.text = message.caption if message.caption else message.text

                    await asyncio.gather(
                        openai_reactions(bot=bot, message=message, from_samuel=from_samuel),
                        words_reactions(bot=bot, message=message),
                        bot_commands(bot=bot, message=message, from_samuel=from_samuel),
                        mock_users(bot=bot, message=message, from_samuel=from_samuel, from_debug_chats=from_debug_chats),
                    )

        elif not bot.debug_mode:
            bot.loop.create_task(
                bot.leave_chat(
                    chat_id=message.chat.id
                )
            )

    elif incoming.edited_message is not None:
        bot.loop.create_task(
            bot.send_message(
                message_text=random.choice(MOCK_EDITS),
                chat_id=incoming.edited_message.chat.id,
                reply_to=incoming.edited_message.message_id
            )
        )

        bot.loop.create_task(telegram_logging(str(incoming)))
