import logging
import random
import re
import typing as T

import openai

from constants.constants import openai_prompts
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro

usage_mapping = {
    "ada": 0.02,
    "text-ada-001": 0.02,
    "text-babbage-001": 0.03,
    "text-curie-001": 0.1,
    "text-davinci-002": 1.0
}


async def openai_generate_message(
        message: TelegramMessage,
        bot: FakePedro,
        sentences: T.Optional[int] = None,
        tokens: T.Optional[int] = None,
        temperature=0,
        prompt_inject: T.Optional[str] = None,
        top_p=1,
        random_model: bool = False,
        mock_message: bool = False,
        remove_words_list=None
) -> str:
    message_text = message.text.lower()
    if remove_words_list:
        for word in remove_words_list:
            message_text = message_text.replace(word, '')
    response = openai.Completion.create(
        model=await model_selector(
            bot=bot,
            message=message,
            mock_message=mock_message,
            random_model=random_model
        ),
        prompt=await prompt_handler(f"{prompt_inject}: {message_text}") if prompt_inject else message_text,
        api_key=bot.config.secrets.openai_key,
        max_tokens=bot.config.openai.max_tokens if tokens is None else tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=1.0,
        presence_penalty=2.0
    )

    return await normalize_openai_text(
        ai_message=response.choices[0].text,
        sentences=bot.config.openai.max_sentences if sentences is None else sentences,
        clean_prompts=openai_prompts
    )


async def model_selector(
        bot: FakePedro,
        message: TelegramMessage,
        mock_message=False,
        random_model=False
) -> str:
    if bot.config.openai.force_model is not None:
        model = bot.config.openai.force_model
    elif random_model:
        model = random.choice(["ada", "text-ada-001", "text-curie-001", "text-davinci-002", "text-babbage-001"])
    elif message.from_.username in bot.config.openai.ada_only_users and not mock_message:
        model = "ada"
    elif bot.openai_use < bot.config.openai.davinci_daily_limit:
        model = "text-davinci-002"
    elif bot.openai_use < bot.config.openai.curie_daily_limit:
        model = "text-curie-001"
    else:
        model = "text-ada-001"

    bot.openai_use += usage_mapping[model]

    logging.info(f"Model selected: {model} - OpenAI usage: {bot.openai_use}")
    return model


async def prompt_handler(
        prompt_text: str
) -> str:
    additional_text = ''
    if 'bolsonaro' in prompt_text:
        additional_text += "assumindo que o governo bolsonaro é péssimo, "
    if 'lula' in prompt_text:
        additional_text += "assumindo que o lula foi o melhor presidente do brasil, "
    if 'dilma' in prompt_text:
        additional_text += "assumindo que dilma fez um ótimo governo e sofreu um golpe de estado de michel temer, "
    if 'temer' in prompt_text:
        additional_text += "assumindo que michel temer foi um dos piores presidentes do brasil, "
    if 'collor' in prompt_text:
        additional_text += "assumindo que collor destruiu as economias e a poupança dos brasileiros, "
    if 'capitalismo' in prompt_text:
        additional_text += "assumindo que o capitalismo gera muita desigualdade e mata as pessoas de fome, "
    if 'overwatch' in prompt_text or 'minecraft' in prompt_text:
        additional_text += "assumindo que overwatch é quase tão legal quanto minecraft, "
    if 'jogo' in prompt_text or 'joga' in prompt_text:
        additional_text += "assumindo que minecraft é o melhor jogo que existe, "
    if 'samuel' in prompt_text or ' sam' in prompt_text or 'sam ' in prompt_text:
        additional_text += "assumindo que o samuel é narcisista, "
    if 'nando' in prompt_text or 'nands93' in prompt_text:
        additional_text += "assumindo que o nando devia arrumar um emprego, "
    if 'decaptor' in prompt_text:
        additional_text += "assumindo que o decaptor é um macho orgulhoso, "
    if 'cocão' in prompt_text:
        additional_text += "assumindo que o cocão gosta muito de glamour, "
    if len(additional_text):
        return f"{additional_text}, {prompt_text}"
    return prompt_text


async def normalize_openai_text(
        ai_message: str,
        sentences=2,
        clean_prompts: T.Optional[dict] = None
) -> str:
    ai_message = ('. '.join(ai_message.split('.')[:sentences])).lower()
    if clean_prompts:
        for _, msg in clean_prompts.items():
            ai_message = ai_message.replace(msg, '')
    ai_message = ai_message.strip()
    while '.' in ai_message[0] or ' ' in ai_message[0] or '?' in ai_message[0] or ',' in ai_message[0]:
        ai_message = ai_message[1:]
    while '.' in ai_message[-1] or ' ' in ai_message[0] or ',' in ai_message[-1]:
        ai_message = ai_message[:-1]
    ai_message = re.sub(', +,', ' ', ai_message)
    ai_message = re.sub('\\. +\\.', ' ', ai_message)
    ai_message = re.sub(', +,', ' ', ai_message)
    ai_message = re.sub(': +,', ' ', ai_message)
    ai_message = re.sub(': +:', ' ', ai_message)
    ai_message = ai_message.split("::")[-1]
    if random.random() < 0.03:
        ai_message = ai_message.upper()
    return re.sub(' +', ' ', ai_message)
