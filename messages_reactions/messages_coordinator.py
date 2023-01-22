import asyncio

from data_classes.received_message import TelegramMessage
from messages_reactions.mock_users import mock_users
from pedro_leblon import FakePedro
from messages_reactions.ai_reactions import openai_reactions
from messages_reactions.bot_commands import bot_commands
from messages_reactions.general_text_reactions import words_reactions
from messages_reactions.image_reactions import image_reactions
from utils.openai_utils import openai_generate_message


async def messages_coordinator(
        bot: FakePedro,
        message: TelegramMessage
) -> None:
    from_samuel = message.from_.is_premium
    from_debug_chats = message.chat.id in (-20341310, 8375482)

    if message.chat.id in bot.allowed_list:
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
