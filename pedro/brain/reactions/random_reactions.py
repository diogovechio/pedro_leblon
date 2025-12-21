# Internal
import random

# Project
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.daily_flags import Flags
from pedro.data_structures.telegram_message import Message


async def random_reactions(
        message: Message,
        telegram: Telegram,
        user_data: UserDataManager,
        daily_flags: Flags,
) -> None:
    user = user_data.get_user_data(message.from_.id)

    if user.tease_messages and random.random() < 0.2 and not daily_flags.random_tease_message:
        daily_flags.random_tease_message = True

        await telegram.send_message(
            message_text=random.choice(user.tease_messages),
            chat_id=message.chat.id,
            sleep_time=3 + (round(random.random()) * 4)
        )
