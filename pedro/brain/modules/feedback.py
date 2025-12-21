# Internal
from contextlib import contextmanager
import asyncio
import random
import typing as T

# External

# Project
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.telegram import Telegram


async def _is_taking_too_long(telegram: Telegram, chat_id: int, user="", max_loops=5, timeout=10, memory: T.Optional[ChatHistory] = None):
    if user:
        messages = [f"@{user} já vou responder",
                    f"@{user} só 1 minuto"]

        for _ in range(max_loops):
            await asyncio.sleep(timeout + int(random.random() * timeout / 5))

            message = random.choice(messages)
            messages.remove(message)

            if memory:
                await memory.add_message(message, chat_id=chat_id)

            asyncio.create_task(
                telegram.send_message(
                    message_text=message,
                    chat_id=chat_id
                )
            )

            timeout *= 1.5


@contextmanager
def sending_action(
        telegram: Telegram,
        chat_id: int,
        user="",
        action: T.Union[T.Literal['typing'], T.Literal['upload_photo'], T.Literal['find_location']] = 'typing',
        memory=None
):
    sending = asyncio.create_task(telegram.send_action(chat_id, action, True))
    timer = asyncio.create_task(_is_taking_too_long(telegram=telegram, chat_id=chat_id, user=user, memory=memory))
    try:
        yield
    finally:
        sending.cancel()
        timer.cancel()
