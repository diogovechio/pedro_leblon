import random

import openai

from constants.constants import openai_block_words, openai_react_words, openai_default_params, openai_prompts
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.openai_utils import model_selector, prompt_handler, normalize_openai_text


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
                    prompt=await prompt_handler(f"{openai_prompts['fale']}: {message.text.lower()}"),
                    api_key=bot.config.openai.api_key,
                    max_tokens=bot.config.openai.max_tokens,
                    **openai_default_params
                )
                bot.loop.create_task(
                    bot.send_message(
                        message_text=await normalize_openai_text(
                            ai_message=response.choices[0].text,
                            sentences=bot.config.openai.max_sentences,
                            clean_prompts=openai_prompts
                        ),
                        chat_id=message.chat.id,
                        sleep_time=1 + (round(random.random()) * 5),
                        reply_to=message.message_id)
                )
                break

    if not openai_block_word_detected and 'pedr' in message.text.lower()[0:4]:
        question = '?' in message.text.lower()
        normalized_message_text = message.text.lower().replace('pedro', '')
        response = openai.Completion.create(
            model=await model_selector(bot, message),
            prompt=await prompt_handler(
                (f"{openai_prompts['fale'] if not question else openai_prompts['responda']}: "
                 f"{normalized_message_text}")),
            api_key=bot.config.openai.api_key,
            max_tokens=bot.config.openai.max_tokens,
            **openai_default_params
        )
        if len(response.choices[0].text):
            bot.loop.create_task(
                bot.send_message(
                    message_text=await normalize_openai_text(
                        ai_message=response.choices[0].text,
                        sentences=bot.config.openai.max_sentences,
                        clean_prompts=openai_prompts
                    ),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )
    elif not openai_block_word_detected:
        if random.random() < bot.config.random_params.random_mock_frequency:
            response = openai.Completion.create(
                model=await model_selector(bot=bot, message=message, random_model=True),
                prompt=await prompt_handler(f"{openai_prompts['comente']}: {message.text.lower()}"),
                api_key=bot.config.openai.api_key,
                max_tokens=bot.config.openai.max_tokens,
                **openai_default_params
            )
            bot.loop.create_task(
                bot.send_message(
                    message_text=await normalize_openai_text(
                        ai_message=response.choices[0].text,
                        sentences=bot.config.openai.max_sentences,
                        clean_prompts=openai_prompts
                    ),
                    chat_id=message.chat.id,
                    sleep_time=1 + (round(random.random()) * 5),
                    reply_to=message.message_id)
            )
