# Project
from pedro.data_structures.telegram_message import Message
from pedro.brain.modules.telegram import Telegram


async def poll_reaction(message: Message, telegram: Telegram):
    if message.poll:
        await telegram.send_reaction(chat_id=message.chat.id, message_id=message.message_id, emoji="💩")
