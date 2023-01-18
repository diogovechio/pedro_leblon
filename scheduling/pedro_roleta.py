import json
import logging
import random

import openai

from pedro_leblon import FakePedro
from utils.openai_utils import normalize_openai_text


def pedro_roleta(bot: FakePedro) -> None:
    try:
        for _id in filter(
                lambda chat_id:
                chat_id < 0 and chat_id not in bot.config.not_internal_chats,
                bot.allowed_list
        ):
            bot.loop.create_task(
                send_roleta(bot, _id)
            )
    except Exception as exc:
        logging.exception(exc)

async def send_roleta(bot: FakePedro, chat_id: int) -> None:
    async with bot.session.get(
        "https://keyo.me/bot/roleta.json"
    ) as roleta:
        roleta_read = json.loads(await roleta.content.read())

        choiced_roleta = random.choice(
            [value for _, value in roleta_read.items()
             if value['text'] is not None and len(value['text']) > 25]
        )['text']

        bot.loop.create_task(
            bot.send_message(
                message_text=(
                    await normalize_openai_text(
                        ai_message=openai.Completion.create(
                            model="text-davinci-003",
                            prompt=f"repita essa frase e em seguinte dê a sua conclusão: '{choiced_roleta}'",
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
                sleep_time=1 + (round(random.random()) * 480)
            )
        )
