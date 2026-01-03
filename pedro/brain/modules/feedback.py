# Internal
from contextlib import contextmanager
from dataclasses import dataclass, field
import asyncio
import random
import typing as T

# External

# Project
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.telegram import Telegram


@dataclass
class FeedbackState:
    """Container to hold the message_id of the last delay message sent.
    
    This is used to track delay messages so they can be edited later
    instead of sending a new message with the final response.
    """
    last_delay_message_id: T.Optional[int] = None


async def _is_taking_too_long(
    telegram: Telegram,
    chat_id: int,
    user: str = "",
    max_loops: int = 5,
    timeout: int = 15,
    memory: T.Optional[ChatHistory] = None,
    feedback_state: T.Optional[FeedbackState] = None
):
    """
    Send delay messages when processing takes too long.
    
    Args:
        telegram: Telegram client instance.
        chat_id: The chat ID to send messages to.
        user: Username to mention in delay messages.
        max_loops: Maximum number of delay messages to send.
        timeout: Initial timeout before first message (seconds).
        memory: Optional chat history to log messages.
        feedback_state: Optional state container to store the last message_id.
    """
    if user:
        messages = [
            f"@{user} já vou responder",
            f"@{user} só 1 minuto"
        ]

        for _ in range(max_loops):
            await asyncio.sleep(timeout + int(random.random() * timeout / 5))

            message = random.choice(messages)
            messages.remove(message)

            if memory:
                await memory.add_message(message, chat_id=chat_id)

            # Send message and capture message_id
            msg_id = await telegram.send_message(
                message_text=message,
                chat_id=chat_id
            )

            # Store the last message_id in the feedback state for later editing
            if feedback_state is not None and msg_id:
                feedback_state.last_delay_message_id = msg_id

            timeout = int(timeout * 1.5)


@contextmanager
def sending_action(
        telegram: Telegram,
        chat_id: int,
        user: str = "",
        action: T.Union[T.Literal['typing'], T.Literal['upload_photo'], T.Literal['find_location']] = 'typing',
        memory: T.Optional[ChatHistory] = None,
        feedback_state: T.Optional[FeedbackState] = None
):
    """
    Context manager that sends typing action and delay messages while processing.
    
    Args:
        telegram: Telegram client instance.
        chat_id: The chat ID to send actions to.
        user: Username to mention in delay messages. If empty, no delay messages are sent.
        action: The chat action to send (typing, upload_photo, find_location).
        memory: Optional chat history to log delay messages.
        feedback_state: Optional state container to track the last delay message_id.
    """
    sending = asyncio.create_task(telegram.send_action(chat_id, action, True))
    timer = asyncio.create_task(_is_taking_too_long(
        telegram=telegram,
        chat_id=chat_id,
        user=user,
        memory=memory,
        feedback_state=feedback_state
    ))
    try:
        yield
    finally:
        sending.cancel()
        timer.cancel()

