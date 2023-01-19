import json
import logging
import random

import openai

from pedro_leblon import FakePedro
from utils.openai_utils import normalize_openai_text
from utils.roleta_utils import get_roletas_from_pavuna

def pedro_roleta(bot: FakePedro) -> None:
    try:
        bot.loop.create_task(
            send_roleta(bot)
        )
    except Exception as exc:
        logging.exception(exc)

async def send_roleta(bot: FakePedro) -> None:
    roleta_list = await get_roletas_from_pavuna(bot, 25)

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

            bot.loop.create_task(
                bot.send_message(
                    message_text=(
                        await normalize_openai_text(
                            ai_message=openai.Completion.create(
                                model="text-davinci-003",
                                prompt=f"repita essa frase e em seguinte dê a sua conclusão: '{random.choice(roleta_list)}'",
                                api_key=bot.config.secrets.openai_key,
                                max_tokens=bot.config.openai.max_tokens,
                                frequency_penalty=1.0,
                                presence_penalty=2.0,
                                temperature=1.0
                            ).choices[0].text,
                            sentences=bot.config.openai.max_sentences
                        )
                    ).upper(),
                    chat_id=chat_id,
                    sleep_time=1 + (round(random.random()) * 10),
                    reply_to=random.choice(messages_ids) if len(messages_ids) else None
                )
            )
