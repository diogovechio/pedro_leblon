import logging
from youtube_transcript_api import YouTubeTranscriptApi
import random
import re
import typing as T
from asyncio import get_running_loop
from bs4 import BeautifulSoup

from data_classes.received_message import TelegramMessage
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


async def youtube_caption_extractor(url: str, char_limit: int) -> str:
    try:
        if "watch?v=" in url and "youtube" in url:
            video_id = url.split("watch?v=")[-1]
        elif "youtu.be" or "shorts" in url:
            video_id = url.split("/")[-1]
        else:
            return ""

        a = YouTubeTranscriptApi.get_transcript(video_id, ['pt-BR', 'pt', 'pt-PT', 'en', 'en-US'])

        text = "\n".join([i['text'] for i in a if 'text' in i])
        if len(text) > char_limit:
            text = text[:int(char_limit/2)] + text[-int(char_limit/2):]

        return text
    except Exception as exc:
        get_running_loop().create_task(telegram_logging(exc))

        return ""


async def html_paragraph_extractor(text: str, char_limit: int) -> str:
    soup = BeautifulSoup(text, 'html.parser')
    if soup.find("article"):
        tag = soup.article
    elif soup.find("main"):
        tag = soup.main
    elif soup.find("body"):
        tag = soup.body
    else:
        return ""

    final_text = "\n".join(
        [text for text in tag.strings
         if len(text.strip()) > 1]
    )

    if len(text) > char_limit:
        final_text = final_text[:int(char_limit / 2)] + final_text[-int(char_limit / 2):]

    return final_text


async def message_destroyer(message_text: str, extra_text=True) -> str:
    message_text = message_text.lower()

    if round(random.random()):
        message_text = message_text.replace('a', ' pqp ')
        message_text = message_text.replace('o', ' pinto ')
    if round(random.random()):
        message_text = message_text.replace('c', ' bosta ')
        message_text = message_text.replace('b', ' cu ')
    if round(random.random()):
        message_text = message_text.replace('l', ' cérebro ')
        message_text = message_text.replace('h', '')
        message_text = message_text.replace('m', 'n')
    if round(random.random()):
        message_text = message_text.replace('t', ' rolão ')
        message_text = message_text.replace('f', ' wololo ')
    else:
        message_text = "tomei no cu"

    if extra_text:
        return "Transforme essa mensagem em algo legível: " + message_text
    return message_text


async def pre_biased_prompt(full_text: str, last_words: str = "", always_ironic=False) -> str:
    extra_irony = f"pedro costuma ser extremamente sarcástico e nada educado.\n" \
                  f"pedro nunca deixa claro quando está apenas brincando e não costuma se desculpar.\n\n"

    additional_text = ''

    if 'bolsonaro' in full_text:
        additional_text += "pedro considera o governo bolsonaro é péssimo e irresponsável.\n"
    if 'lula' in full_text:
        additional_text += "pedro considera o lula foi o melhor presidente do brasil.\n"
    if 'president' in full_text:
        additional_text += "estamos em 2023 e lula é o atual presidente do brasil.\n"
    if 'dilma' in full_text:
        additional_text += "pedro considera  que a dilma fez um ótimo governo.\n"
    if 'temer' in full_text:
        additional_text += "pedro considera michel temer um dos piores presidentes do brasil.\n"

    if 'samuel' in last_words or ' sam ' in last_words in last_words:
        additional_text += "pedro considera que o samuel (também conhecido como samuelgames) é um narcisista.\n"
    if 'nando' in last_words or 'nands93' in last_words:
        additional_text += "pedro entende que o nando (tambem conhecido como @nands93) devia arrumar um emprego.\n"
    if 'renato' in last_words or 'renfd' in last_words:
        additional_text += "pedro sabe que o renato é um bolsominion homofóbico.\n"
    if 'decaptor' in last_words or 'andré' in last_words or 'andre' in last_words:
        additional_text += "pedro considera o decaptor (também conhecido como andré milani) um macho orgulhoso.\n"
    if 'eicho' in last_words:
        additional_text += "pedro sabe que o eicho gosta de uma tretinha.\n"
    if 'diogo' in last_words:
        additional_text += "pedro sabe que o diogo às vezes reclama demais.\n"
    if 'thomma' in last_words or 'tomas' in last_words or 'tomaz' in last_words or 'thoma' in last_words:
        additional_text += f"segundo a forbes, thommaz é um dos poucos quadrilionários no brasil com uma " \
                           f"fortuna estimada em {round(random.random() * 24)} quadrilões de dólares.\n"
    if 'keyo' in last_words:
        additional_text += "pedro sabe que o keyo é rica e não gosta de gentalha.\n"
    if 'cocão' in last_words or 'cocao' in last_words:
        additional_text += "pedro percebe que o cocão gosta muito de glamour.\n"

    if len(additional_text):
        return f"considere que o pedro tem essas opiniões:\n" \
               f"{additional_text}\n" \
               f"{'acima de tudo,' + extra_irony if random.random() < 0.4 else ''}" \
               f"segue abaixo a conversa:\n\n" \
               f"{full_text}"

    if random.random() < 0.4 or always_ironic:
        full_text = f"{extra_irony}segue abaixo a conversa:\n\n{full_text}"

    return full_text


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
        ai_message = ""
        idx_to_lower = 0
        if "```" not in original_message:
            original_message = original_message.strip()
            for i, letter in enumerate(original_message):
                if idx_to_lower == i:
                    letter = letter.lower()
                ai_message += letter

                if letter in (".", "!", "?"):
                    idx_to_lower = i + 2
                elif letter == '"':
                    idx_to_lower = i + 1
        else:
            ai_message = original_message

        if ai_message.count(".") == 1 and ai_message[-1] == ".":
            ai_message = ai_message.replace(".", "")

        if clean_prompts:
            for _, msg in clean_prompts.items():
                ai_message = ai_message.replace(msg, '')

        ai_message = ai_message.replace("pedro: ","rs, ")

        if ai_message:
            while any(word in ai_message[0] for word in ['.', ',', '?', '\n', ' ', '!']):
                ai_message = ai_message[1:]

            if '"' in ai_message[0] and '"' in ai_message[-1]:
                ai_message = ai_message.replace('"',"")

            if random.random() < 0.05:
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


def create_username(first_name: str, username: T.Optional[str]) -> str:
    user_name = first_name
    if username:
        user_name = f"{first_name} ({username})"

    return user_name
