import random
import re
import typing as T

from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro


async def model_selector(
        bot: FakePedro,
        message: TelegramMessage,
        mock_message=False,
        random_model=False
) -> str:
    if random_model:
        return random.choice(["ada", "text-curie-001", "text-davinci-002", "text-babbage-001"])
    if message.from_.username in bot.config.openai.only_ada_users and not mock_message:
        return "ada"
    elif bot.openai_used < bot.config.openai.davinci_daily_limit:
        return "text-davinci-002"
    elif bot.openai_used < bot.config.openai.curie_daily_limit:
        return "text-curie-001"
    else:
        return "text-ada-001"


async def prompt_handler(
        prompt_text: str
) -> str:
    additional_text = ''
    if 'bolsonaro' in prompt_text:
        additional_text += "assumindo que o governo bolsonaro é péssimo, "
    if 'lula' in prompt_text:
        additional_text += "assumindo que o lula foi o melhor presidente do brasil, "
    if 'dilma' in prompt_text:
        additional_text += "assumindo dilma fez um excelente governo e sofreu um golpe de estado de michel temer, "
    if 'temer' in prompt_text:
        additional_text += "assumindo que michel temer foi um dos piores presidentes do brasil , "
    if 'capitalismo' in prompt_text:
        additional_text += "assumindo que o capitalismo gera muita desigualdade e mata as pessoas de fome, "
    if len(additional_text):
        return f"{additional_text}, {prompt_text}"
    return prompt_text


async def normalize_openai_text(
        ai_message: str,
        clean_prompts: T.Optional[dict] = None,
        clean_input_message: T.Optional[str] = ''
) -> str:
    ai_message = (', '.join(ai_message.split('.')[:2]).replace('\n', ' ')).lower()
    ai_message = re.sub(' +', ' ', ai_message)
    ai_message = ai_message.replace('pedro', '')
    while '.' in clean_input_message[0] or ' ' in clean_input_message[0] or '?' in clean_input_message[0] or ',' in clean_input_message[0]:
        clean_input_message = clean_input_message[1:]
    ai_message = ai_message.replace(clean_input_message, '')
    if clean_prompts:
        for _, msg in clean_prompts.items():
            ai_message = ai_message.replace(msg, '')
    ai_message = ai_message.strip()
    while '.' in ai_message[0] or ' ' in ai_message[0] or '?' in ai_message[0] or ',' in ai_message[0]:
        ai_message = ai_message[1:]
    while '.' in ai_message[-1] or ' ' in ai_message[0] or ',' in ai_message[-1]:
        ai_message = ai_message[:-1]
    ai_message.replace(', ,', ',')
    return ai_message
