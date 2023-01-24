import asyncio
import logging
import random
import re
import typing as T

import openai

from constants.constants import OPENAI_PROMPTS
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro

usage_mapping = {
    "ada": 0.02,
    "text-ada-001": 0.02,
    "text-babbage-001": 0.03,
    "text-curie-001": 0.1,
    "text-davinci-003": 1.0
}


async def openai_generate_message(
        message_data: TelegramMessage,
        message_text: str,
        bot: FakePedro,
        sentences: T.Optional[int] = None,
        tokens: T.Optional[int] = None,
        temperature=0,
        prompt_inject: T.Optional[str] = None,
        message_text_replace: T.Optional[str] = None,
        force_model: T.Optional[str] = None,
        top_p=1,
        random_model: bool = False,
        mock_message: bool = False,
        destroy_message: bool = False,
        remove_words_list=None
) -> str:
    message_text = message_text.lower()

    if destroy_message:
        message_text = message_text.replace('a', 'o')
        message_text = message_text.replace('o', 'a')
        message_text = message_text.replace('c', 'b')
        message_text = message_text.replace('b', 't')
        message_text = message_text.replace('l', 'a')
        message_text = message_text.replace('h', '')
        message_text = message_text.replace('m', 't')

        force_model = "text-ada-001"

        message_text = "Transforme essa mensagem em algo legível: " + message_text

    if remove_words_list:
        for word in remove_words_list:
            message_text = message_text.replace(word, '')

    if message_text_replace:
        message_text = message_text_replace

    try:
        response = await asyncio.wait_for(
            openai_completion(
                bot=bot,
                message_data=message_data,
                mock_message=mock_message,
                random_model=random_model,
                force_model=force_model,
                prompt_inject=prompt_inject,
                tokens=tokens,
                message_text=message_text,
                temperature=temperature,
                top_p=top_p
            ),
            timeout=60
        )
    except Exception as exc:
        logging.exception(exc)
        return "meu cérebro tá fora do ar"

    return await normalize_openai_text(
        ai_message=response.choices[0].text,
        sentences=bot.config.openai.max_sentences if sentences is None else sentences,
        clean_prompts=OPENAI_PROMPTS
    )


async def openai_completion(
        bot: FakePedro,
        message_data: TelegramMessage,
        mock_message: bool,
        random_model: bool,
        force_model: T.Optional[str] = None,
        prompt_inject: T.Optional[str] = None,
        tokens: T.Optional[int] = None,
        message_text: str = '',
        temperature=0,
        top_p=1
):
    return openai.Completion.create(
        model=await model_selector(
            bot=bot,
            message=message_data,
            mock_message=mock_message,
            random_model=random_model
        ) if not force_model else force_model,
        prompt=await prompt_handler(f"{prompt_inject}: {message_text}") if prompt_inject else message_text,
        api_key=bot.config.secrets.openai_key,
        max_tokens=bot.config.openai.max_tokens if tokens is None else tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=1.0,
        presence_penalty=2.0
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
        model = random.choice(["ada", "text-ada-001", "text-curie-001", "text-davinci-003", "text-babbage-001"])
    elif message.from_.username in bot.config.openai.ada_only_users and not mock_message:
        model = "ada"
    elif bot.openai_use < bot.config.openai.davinci_daily_limit:
        model = "text-davinci-003"
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
    if 'guax' in prompt_text:
        additional_text += "assumindo que o guax é furry, "
    if 'eicho' in prompt_text:
        additional_text += "assumindo que o eicho gosta de uma tretinha, "
    if 'diogo' in prompt_text:
        additional_text += "assumindo que o diogo adora reclamar, "
    if 'thomma' in prompt_text or 'tomas' in prompt_text or 'tomaz' in prompt_text or 'thoma' in prompt_text:
        additional_text += "assumindo que o thommaz é quadrilionário, "
    if 'keyo' in prompt_text:
        additional_text += "assumindo que o keyo é rica e odeia gentalha, "
    if 'samuel' in prompt_text or ' sam' in prompt_text or 'sam ' in prompt_text:
        additional_text += "assumindo que o verdadeiro nome do samuel é samuelgames, "
    if 'nando' in prompt_text or 'nands93' in prompt_text:
        additional_text += "assumindo que o nando devia arrumar um emprego, "
    if 'renato' in prompt_text or 'renfd' in prompt_text:
        additional_text += "assumindo que o renato é um bolsominion homofóbico, "
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
    try:
        ai_message = (
            '. '.join(
                list(
                    filter(
                        lambda entry: re.sub(" +", '', entry) != '', ai_message.split('.')
                    )
                )[:sentences]
            )
        ).lower()

        if clean_prompts:
            for _, msg in clean_prompts.items():
                ai_message = ai_message.replace(msg, '')

        ai_message = re.sub(', +,', ' ', ai_message)
        ai_message = re.sub('\\. +\\.', ' ', ai_message)
        ai_message = re.sub(', +,', ' ', ai_message)
        ai_message = re.sub(': +,', ' ', ai_message)
        ai_message = re.sub(': +:', ' ', ai_message)
        ai_message = ai_message.split("::")[-1]
        ai_message = ai_message.strip()

        if ai_message:
            logging.info(ai_message)

            while any(word in ai_message[0] for word in ['.', ',', '?', ' ']):
                ai_message = ai_message[1:]

            while any(word in ai_message[-1] for word in ['.', ',', '?', ' ']):
                ai_message = ai_message[:-1]

            if random.random() < 0.03:
                ai_message = ai_message.upper()

            return re.sub(' +', ' ', ai_message)
        else:
            return 'estou sem palavras' if round(random.random()) else 'tenho nada a dizer'
    except Exception as exc:
        logging.exception(exc)

        return '@diogovechio dei pau vai ver o log'
