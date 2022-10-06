import logging
import random
import re
import typing as T

from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro

usage_mapping = {
    "ada": 0.02,
    "text-ada-001": 0.02,
    "text-babbage-001": 0.03,
    "text-curie-001": 0.1,
    "text-davinci-002": 1.0
}


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
    elif message.from_.username in bot.config.openai.only_ada_users and not mock_message:
        model = "ada"
    elif bot.openai_used < bot.config.openai.davinci_daily_limit:
        model = "text-davinci-002"
    elif bot.openai_used < bot.config.openai.curie_daily_limit:
        model = "text-curie-001"
    else:
        model = "text-ada-001"

    bot.openai_used += usage_mapping[model]

    logging.info(f"Model selected: {model} - OpenAI usage: {bot.openai_used}")
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
    if 'overwatch' in prompt_text:
        additional_text += "assumindo que overwatch é um jogo chato e minecraft é mais divertido, "
    if 'jogo' in prompt_text or 'jogar' in prompt_text or 'jogando' in prompt_text:
        additional_text += "assumindo que minecraft é o melhor jogo que existe, "
    if len(additional_text):
        return f"{additional_text}, {prompt_text}"
    return prompt_text


async def normalize_openai_text(
        ai_message: str,
        sentences=2,
        clean_prompts: T.Optional[dict] = None
) -> str:
    ai_message = (', '.join(ai_message.split('.')[:sentences]).replace('\n', ' ')).lower()
    ai_message = ai_message.replace('pedro', '')
    if clean_prompts:
        for _, msg in clean_prompts.items():
            ai_message = ai_message.replace(msg, '')
    ai_message = ai_message.strip()
    while '.' in ai_message[0] or ' ' in ai_message[0] or '?' in ai_message[0] or ',' in ai_message[0]:
        ai_message = ai_message[1:]
    while '.' in ai_message[-1] or ' ' in ai_message[0] or ',' in ai_message[-1]:
        ai_message = ai_message[:-1]
    ai_message = re.sub(', +,', ' ', ai_message)
    ai_message = re.sub(': +,', ' ', ai_message)
    if random.random() < 0.03:
        ai_message = ai_message.upper()
    return re.sub(' +', ' ', ai_message)
