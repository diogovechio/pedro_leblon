import random

import openai

from constants.constants import openai_block_words, openai_react_words, openai_default_params
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.openai_utils import model_selector
from utils.text_utils import normalize_openai_text


async def openai_reactions(
        bot: FakePedro, message:
        TelegramMessage
) -> None:
    openai_block_word_detected = False
    for block_word in openai_block_words:
        if openai_block_word_detected := block_word in message.text.lower():
            break

    if not openai_block_word_detected:
        for react_word in openai_react_words:
            if '?' not in message.text.lower() and react_word in message.text.lower(

            ) and random.random() < bot.config.random_params.words_react_frequency:
                response = openai.Completion.create(
                    model=await model_selector(bot=bot, message=message, mock_message=True),
                    prompt=f"fale sobre esse tema: {message.text.lower()}",
                    api_key=bot.config.openai.api_key,
                    **openai_default_params
                )
                bot.loop.create_task(
                    bot.send_message(
                        message_text=await normalize_openai_text(response.choices[0].text),
                        chat_id=message.chat.id,
                        sleep_time=1 + (round(random.random()) * 5),
                        reply_to=message.message_id)
                )
                bot.openai_used += 1
                break

    if not openai_block_word_detected and 'pedr' in message.text.lower()[0:4]:
        question = '?' in message.text.lower()
        response = openai.Completion.create(
            model=await model_selector(bot, message),
            prompt=(f"{'fale sobre esse tema' if not question else 'responda essa pergunta'}: "
                    f"{message.text.lower().replace('pedro', '')}"),
            api_key=bot.config.openai.api_key,
            **openai_default_params
        )
        if len(response.choices[0].text):
            bot.loop.create_task(
                bot.send_message(
                    message_text=await normalize_openai_text(response.choices[0].text),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )
            bot.openai_used += 1
    elif not openai_block_word_detected:
        if random.random() < bot.config.random_params.random_mock_frequency:
            response = openai.Completion.create(
                model=await model_selector(bot=bot, message=message, random_model=True),
                prompt=f"comente sobre isso: {message.text.lower()}",
                api_key=bot.config.openai.api_key,
                **openai_default_params
            )
            bot.loop.create_task(
                bot.send_message(
                    message_text=await normalize_openai_text(response.choices[0].text),
                    chat_id=message.chat.id,
                    sleep_time=1 + (round(random.random()) * 5),
                    reply_to=message.message_id)
            )
            bot.openai_used += 1
