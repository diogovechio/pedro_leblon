from youtube_transcript_api import YouTubeTranscriptApi
import random
import re
import typing as T
from asyncio import get_running_loop
from bs4 import BeautifulSoup
from unidecode import unidecode

from pedro_leblon import telegram_logging
from constants.constants import PEDRO_USERS_OPINIONS, PEDRO_GENERAL_OPINIONS, STOPWORDS


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
            text = text[:int(char_limit / 2)] + text[-int(char_limit / 2):]

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

    if len(final_text) < 500:
        if soup.find("main"):
            tag = soup.main

        elif soup.find("body"):
            tag = soup.body

        new_text = "\n".join(
            [text for text in tag.strings
             if len(text.strip()) > 1]
        )

        if len(new_text) > len(final_text):
            final_text = new_text

    if len(final_text) > char_limit:
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


async def pre_biased_prompt(
        full_text: str,
        users_opinions: T.Dict[str, T.List[str]],
        last_words: str = ""
) -> str:
    additional_text = ''

    for entity in PEDRO_GENERAL_OPINIONS:
        if entity in full_text.lower():
            additional_text += random.choice(PEDRO_GENERAL_OPINIONS[entity])
            additional_text += "\n"

    friends_text = ""
    friends_names = []

    counter = 0
    for entity_names, opinions in users_opinions.items():
        ignore = entity_names.split("#")
        if "#" in entity_names:
            entity_names = entity_names.split("#")[0]
        names_list = entity_names.split("@")
        if len(ignore) > 1:
            ignore = ignore[-1]
        else:
            ignore = "wololololo"

        for name in names_list:
            name = unidecode(name)
            last_words = unidecode(last_words)

            if name in last_words.lower() and ignore not in last_words.lower() and len(opinions):
                counter += 1
                friends_names.append(name)
                friends_text += f"{counter} - sobre {name}: "
                friends_text += " ".join(opinions) + '\n\n'
                break

    if len(friends_names):
        pre_text = "\n\nesses pessoas são amigas do pedro: "
        pre_text += ", ".join(friends_names)
        pre_text += ".\n\nessas são as opiniões do pedro sobre esses amigos. expresse o que sabe sobre eles sempre que " \
                    "lhe for perguntado:\n"
        pre_text += friends_text
        additional_text += pre_text

    if len(additional_text):
        additional_text = unidecode(additional_text)

        return f"considere que o pedro tem essas opiniões:\n" \
               f"{additional_text}\n" \
               f"segue abaixo a conversa:\n\n" \
               f"{full_text}"

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
        if "```" not in original_message and len(original_message) > 1:
            original_message = original_message.strip()
            for i, letter in enumerate(original_message):
                next_idx = i + 1
                if idx_to_lower == i:
                    if (len(original_message) - 1 != next_idx) and not original_message[next_idx].isupper():
                        letter = letter.lower()
                ai_message += letter

                if letter in (".", "!", "?", ":"):
                    idx_to_lower = i + 2
                elif letter in ('"', "\n"):
                    idx_to_lower = i + 1

            if ai_message.count(".") == 1 and ai_message[-1] == ".":
                ai_message = ai_message.replace(".", "")

            if clean_prompts:
                for _, msg in clean_prompts.items():
                    ai_message = ai_message.replace(msg, '')

            ai_message = ai_message.replace("pedro: ", "rs, ")

            if ai_message:
                while any(word in ai_message[0] for word in ['.', ',', '?', '\n', ' ', '!']):
                    ai_message = ai_message[1:]

                if '"' in ai_message[0] and '"' in ai_message[-1]:
                    ai_message = ai_message.replace('"', "")

                if random.random() < 0.02 or any(word in ai_message for word in [
                    "uau,", "olha só", "que original", "puxa vida", "olha,", "sério mesmo", "que pena ", "desculp", "né?",
                    "tão educado", "esse sujeito", "esse ser ", "que interessante", "não é mesmo", "quem diria"
                ]):
                    ai_message = ai_message.upper()

                if command_in("ah,", ai_message) and round(random.random()):
                    ai_message = ai_message.replace("ah, ", "")

                return re.sub(' +', ' ', ai_message)
            elif len(original_message):
                return original_message.upper()
            else:
                return 'estou sem palavras' if round(random.random()) else 'tenho nada a dizer'
    except Exception as exc:
        get_running_loop().create_task(telegram_logging(exc))

        if len(original_message):
            return original_message.upper()

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


def remove_stopwords(text: str) -> str:
    for word in STOPWORDS:
        text = text.replace(f" {word} ", " ")

    return text
