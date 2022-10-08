import asyncio

from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from processing.ai_reactions import openai_reactions
from processing.bot_commands import bot_commands
from processing.general_text_reactions import words_reactions, mock_users
from processing.image_reactions import image_pipeline


async def messages_coordinator(
        bot: FakePedro,
        message: TelegramMessage
) -> None:
    if message.chat.id in bot.allowed_list:
        from_samuel = message.from_.is_premium
        from_debug_chats = message.chat.id in (-20341310, 8375482)

        if message.photo:
            bot.loop.create_task(
                image_pipeline(
                    bot=bot,
                    message=message,
                    method='cropper' if from_samuel or from_debug_chats else 'face_classifier',
                    always_send_crop=from_debug_chats
                )
            )

        if message.text:
            await asyncio.gather(
                openai_reactions(bot=bot, message=message),
                words_reactions(bot=bot, message=message),
                bot_commands(bot=bot, message=message, from_samuel=from_samuel),
                mock_users(bot=bot, message=message, from_samuel=from_samuel, from_debug_chats=from_debug_chats),
            )
