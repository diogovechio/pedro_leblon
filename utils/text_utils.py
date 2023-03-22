import logging
import random
import re
import typing as T
from asyncio import get_running_loop

from pedro_leblon import telegram_logging


async def greeter(
        name: str,
        match_result: float = 1.0,
        min_accepted_matches: float = 0.9
) -> str:
    get_running_loop().create_task(telegram_logging(f"{name}: {match_result}"))
    if match_result > min_accepted_matches:
        return random.choice([
            f'{name} fofs',
            f'oi {name}',
            f'tudo bem {name}?',
            f"oi {name} {f'lindo' if round(random.random()) else 'linda'}",
            f'gostei dessa foto {name}'
        ])
    else:
        return f'tenho {round(match_result * 100)}% de certeza que é vc {name}...'


async def message_miguxer(message: str) -> str:
    return ''.join(
        [
            letter.upper() if round(random.random()) else letter.lower()
            for letter in message
        ]
    )

async def https_url_extract(text: str) -> str:
    final_text = ""
    text = text[text.find('https://'):]
    for letter in text:
        if letter == " " or letter == "\n":
            break
        final_text += letter
    if "https://" in final_text:
        return final_text
    else:
        return ""


async def html_paragraph_extractor(text: str) -> str:
    cleaned_html = re.sub("<[^>]*>", "olololo", text)
    split_cleaned_html = cleaned_html.split("olololo")

    split_cleaned_html = [
        x.strip().replace("\n", "") for x in split_cleaned_html
        if len(x.strip()) > 0 and "function(" not in x and "{" not in x and "window." not in x]

    new_split = [""]

    short_len_sequence_block = 4
    for i, text in enumerate(split_cleaned_html):
        text = (text.lower()).strip()

        if (len(text) < short_len_sequence_block and len(new_split[-1]) < short_len_sequence_block) or text == new_split[-1]:
            continue
        else:
            new_split.append(text)

    return ". ".join(new_split)


async def message_destroyer(message_text: str) -> str:
    message_text = message_text.lower()
    message_text = message_text.replace('a', 'o')
    message_text = message_text.replace('o', 'a')
    message_text = message_text.replace('c', 'b')
    message_text = message_text.replace('b', 't')
    message_text = message_text.replace('l', 'a')
    message_text = message_text.replace('h', '')
    message_text = message_text.replace('m', 't')

    return "Transforme essa mensagem em algo legível: " + message_text


async def pre_biased_prompt(prompt_text: str) -> str:
    additional_text = ''
    if 'pedro' in prompt_text:
        additional_text = 'assumindo que o seu próprio nome é pedro, '
    if 'bolsonaro' in prompt_text:
        additional_text += "assumindo que o governo bolsonaro é péssimo, "
    if 'lula' in prompt_text:
        additional_text += "assumindo que o lula foi o melhor presidente do brasil, "
    if 'president' in prompt_text:
        additional_text += "assumindo que estamos em 2023 e lula é o atual presidente do brasil, "
    if 'dilma' in prompt_text:
        additional_text += "assumindo que dilma fez um ótimo governo, "
    if 'temer' in prompt_text:
        additional_text += "assumindo que michel temer foi um dos piores presidentes do brasil, "
    if 'capitalismo' in prompt_text:
        additional_text += "assumindo que o capitalismo gera muita desigualdade, "
    if 'overwatch' in prompt_text or 'minecraft' in prompt_text:
        additional_text += "assumindo que overwatch é quase tão legal quanto minecraft, "
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
    if 'cocão' in prompt_text or 'cocao' in prompt_text:
        additional_text += "assumindo que o cocão gosta muito de glamour, "
    if len(additional_text):
        return f"{additional_text}, {prompt_text}"
    return prompt_text


async def send_message_last_try(message_text: str) -> str:
    message_text = re.sub("[^A-Za-z0-9,.!àèìòùÀÈÌÒÙáéíóúýÁÉÍÓÚÝâêîôûÂÊÎÔÛãñõÃÑÕ]+", " ", message_text)
    if message_text == "":
        message_text = "tenho nada a te dizer"

    return message_text


async def normalize_openai_text(
        original_message: str,
        clean_prompts: T.Optional[dict] = None
) -> str:
    try:
        if "```" not in original_message:
            ai_message = original_message.lower()
        else:
            ai_message = original_message

        if ai_message.count(".") == 1 and ai_message[-1] == ".":
            ai_message = ai_message.replace(".", "")

        if clean_prompts:
            for _, msg in clean_prompts.items():
                ai_message = ai_message.replace(msg, '')

        ai_message = ai_message.replace("pedro: ","rs, ")

        if ai_message:
            get_running_loop().create_task(telegram_logging(ai_message))

            while any(word in ai_message[0] for word in ['.', ',', '?', ' ', '"']):
                ai_message = ai_message[1:]

            while any(word in ai_message[-1] for word in ['"']):
                ai_message = ai_message[:-1]

            if random.random() < 0.03:
                ai_message = ai_message.upper()

            return re.sub(' +', ' ', ai_message)
        elif len(original_message):
            return original_message.upper()
        else:
            return 'estou sem palavras' if round(random.random()) else 'tenho nada a dizer'
    except Exception as exc:
        get_running_loop().create_task(telegram_logging(exc))

        return '@diogovechio dei pau vai ver o log'

def command_in(
        command: str,
        text: str,
        text_end=False
) -> bool:
    if not text_end:
        return command.lower() in text.lower()[0:len(command) + 2]
    else:
        return command.lower() in text.lower()[-(len(command) + 6):]
