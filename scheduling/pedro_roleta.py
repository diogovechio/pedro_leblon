import json
import logging
import random


from pedro_leblon import FakePedro, telegram_logging
from utils.roleta_utils import get_roletas_from_pavuna


def pedro_roleta(bot: FakePedro) -> None:
    try:
        if bot.datetime_now.hour == bot.roleta_hour and bot.last_roleta_day != bot.datetime_now.day:
            bot.loop.create_task(
                send_roleta(bot)
            )

            bot.roleta_hour = round(random.random() * 23)
            bot.last_roleta_day = bot.datetime_now.day
    except Exception as exc:
        bot.loop.create_task(telegram_logging(exc))


async def send_roleta(bot: FakePedro) -> None:
    roleta_list = await get_roletas_from_pavuna(bot, 25)

    if bot.datetime_now.day % 3 == 0:
        for chat_id in filter(
                lambda _chat_id:
                _chat_id < 0 and _chat_id not in bot.config.not_internal_chats,
                bot.allowed_list
        ):
            messages_ids = [
                messages_ids.split(":")[1]
                for messages_ids in bot.interacted_messages_with_chat_id
                if str(chat_id) in messages_ids
            ]
            bot.loop.create_task(bot.send_action(chat_id=chat_id, action="typing"))

            bot.loop.create_task(
                bot.send_message(
                    message_text=(
                        await bot.openai.generate_message(
                            full_text=f"repita essa frase e em seguinte dê a sua conclusão: "
                                         f"'{random.choice(roleta_list)['text']}'",
                        )
                    ).upper(),
                    chat_id=chat_id,
                    sleep_time=1 + (round(random.random()) * 10),
                    reply_to=random.choice(messages_ids) if len(messages_ids) else None
                )
            )
