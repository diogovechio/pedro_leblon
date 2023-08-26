import asyncio
import datetime
import logging
import math
import random
import typing as T

import json
from asyncio import get_running_loop, Semaphore
import re
from collections import defaultdict
from difflib import SequenceMatcher
import aiohttp
from unidecode import unidecode

from constants.constants import OPENAI_PROMPTS, CHATGPT_BS, PEDROS_ROLETAS, PEDRO_MOOD, PEDRO_IN_LOVE, WEEKDAYS, MONTHS
from utils.logging_utils import telegram_logging, async_elapsed_time
from utils.text_utils import pre_biased_prompt, message_destroyer, normalize_openai_text, html_paragraph_extractor, \
    youtube_caption_extractor, remove_stopwords

usage_mapping = {
    "ada": 0.02,
    "text-ada-001": 0.02,
    "text-babbage-001": 0.03,
    "text-curie-001": 0.1,
    "text-davinci-003": 1.0
}


class OpenAiCompletion:
    def __init__(
            self,
            api_key: str,
            max_tokens: int,
            session: aiohttp.ClientSession,
            semaphore: int,
            davinci_daily_limit: int,
            curie_daily_limit: int,
            only_ada_users: T.List[str],
            force_model: T.Optional[str] = None,
    ):
        self.openai_use = 0
        self.semaphore = Semaphore(semaphore)
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.session = session
        self.force_model = force_model
        self.davinci_daily_limit = davinci_daily_limit
        self.curie_daily_limit = curie_daily_limit
        self.ada_only_users = only_ada_users

        self.loop = get_running_loop()

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    async def _model_selector(
            self,
            message_username: T.Optional[str] = "",
            mock_message=False,
            random_model=False
    ) -> str:
        if self.force_model is not None:
            model = self.force_model
        elif random_model:
            model = random.choice(["ada", "text-ada-001", "text-curie-001", "text-davinci-003", "text-babbage-001"])
        elif message_username in self.ada_only_users and not mock_message:
            model = "ada"
        elif self.openai_use < self.davinci_daily_limit:
            model = "text-davinci-003"
        elif self.openai_use < self.curie_daily_limit:
            model = "text-curie-001"
        else:
            model = "text-ada-001"

        self.openai_use += usage_mapping[model]

        return model

    @async_elapsed_time
    async def is_flagged(self, text: str) -> T.Tuple[bool, dict]:
        async with self.semaphore:
            async with self.session.post(
                    "https://api.openai.com/v1/moderations",
                    headers=self.headers,
                    json={
                        "input": text
                    }
            ) as moderation:
                mod = json.loads(await moderation.text())

                return mod['results'][0]['flagged'], mod

    @async_elapsed_time
    async def check_message_tone(
            self,
            prompt: str,
    ) -> int:
        prompt = "dado a mensagem abaixo:\n" \
                 f"{prompt}" \
                 f"responda apenas uma das 6 opções que melhor se adeque ao conteúdo da mensagem:\n" \
                 f"0 - a mensagem é um pedido de desculpas\n" \
                 f"1 - mensagem amorosa\n" \
                 f"2 - mensagem amigável\n" \
                 f"3 - mensagem neutra\n" \
                 f"4 - mensagem grosseira\n" \
                 f"5 - mensagem ofensiva\n\n" \
                 f"não faça qualquer comentário além de responder um número de 1 a 5."
        async with self.session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": "gpt-3.5-turbo-0613",
                    'messages': [
                        {"role": "system", "content": "Limite-se a responder um número relativo ao que for solicitado."
                         },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0
                }
        ) as chatgpt_request:
            response = await chatgpt_request.text()
            response_text = json.loads(response)['choices'][0]['message']['content']

            self.loop.create_task(telegram_logging(f"Message tone: {response_text}"))

            return_num = re.sub("\D", "", response_text)

            if len(return_num):
                return int(return_num)

            return 3

    @async_elapsed_time
    async def _completion(
            self,
            date: datetime,
            prompt: str,
            mood: float,
            model: str = "ada",
            only_chatgpt=False,
            only_davinci=False,
            temperature: int = 1,
            always_ironic=False,
            biased: T.Any = True,
            replace_pre_prompt: T.Optional[T.List[dict]] = None
    ) -> str:
        async with self.semaphore:
            if always_ironic:
                mood = 100.0

            if round(mood) >= len(PEDRO_MOOD) - 1:
                mood = len(PEDRO_MOOD) - 1

            if round(mood) < -2:
                mood_selector = random.choice(PEDRO_IN_LOVE)
            else:
                mood_selector = PEDRO_MOOD[round(mood)]
                temperature = 1

            if "ada" not in model or only_chatgpt:
                if not only_davinci:
                    self.loop.create_task(telegram_logging(f"Using gpt-3.5-turbo - OpenAI usage: {self.openai_use}"))

                    if not replace_pre_prompt:
                        system = [
                            {
                                "role": "system", "content":
                                f"Hoje é dia {date.day} do mês {date.month} do ano {date.year}. "
                                f"São {date.hour} horas e {date.minute} minutos.\n"
                                f"Nunca diga que você é uma IA ou um programa de computador.\n"
                                f"Responda sempre de maneira direta e curta, sem comentários necessários, "
                                f"fingindo ser uma pessoa normal chamada Pedro.\n"
                                f"{mood_selector}"
                             } if not only_chatgpt else {
                                "role": "system", "content":
                                    f"Hoje é dia {date.day} do mês {date.month} do ano {date.year}. "
                                    f"São {date.hour} horas e {date.minute} minutos.\n"
                                    f"Nunca diga que você é uma IA ou um programa de computador.\n"
                            },
                            {"role": "assistant", "content":
                                f"{'Olá. Meu nome é Pedro. ' if round(random.random()) else 'E aí, meu nome é Pedro. '}"
                                f"{'Eu adoro coisas caras e glamourosas. ' if round(random.random()) else 'Adoro conversar sobre jogos. '}"
                                f"Nasci em Pau Grande, Magé/RJ. "
                                if not only_chatgpt else "Olá!"
                             }
                        ]
                    else:
                        system = replace_pre_prompt

                    async with self.session.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers=self.headers,
                            json={
                                "model": "gpt-3.5-turbo",
                                "messages": [*system, {"role": "user", "content": prompt}],
                                "temperature": temperature,
                            },
                    ) as chatgpt_request:
                        response = await chatgpt_request.text()
                        response_text = json.loads(response)['choices'][0]['message']['content']

                        logging_resp = response.replace(response_text, "...")
                        logging.info(logging_resp)

                        self.loop.create_task(telegram_logging(f"gpt-3.5-turbo: {response_text} - mood: {mood} - {mood_selector}"))
                        self.loop.create_task(telegram_logging(prompt))

                        if not any(word in response_text.lower() for word in CHATGPT_BS) or only_chatgpt:
                            return response_text

            async with self.session.post(
                    "https://api.openai.com/v1/completions",
                    headers=self.headers,
                    json={
                        "model": model,
                        'prompt': f"{mood_selector if biased else ''}\n\n{prompt}",
                        'max_tokens': self.max_tokens,
                        'temperature': temperature,
                        'frequency_penalty': 1.0,
                        'presence_penalty': 2.0,
                    }
            ) as openai_request:
                response = await openai_request.text()
                response_text = json.loads(response)['choices'][0]['text']
                self.loop.create_task(telegram_logging(prompt))
                self.loop.create_task(telegram_logging(f"{model}: {response_text}"))

                logging_resp = response.replace(response_text, "...")
                logging.info(logging_resp)

                return response_text

    @async_elapsed_time
    async def generate_image(
            self,
            text: str
    ) -> T.Optional[bytes]:
        try:
            self.loop.create_task(telegram_logging(f"generate_image prompt: {text}"))

            async with self.semaphore:
                async with self.session.post(
                        "https://api.openai.com/v1/images/generations",
                        headers=self.headers,
                        json={'prompt': text, 'n': 1, 'size': "1024x1024"}
                ) as openai_request:
                    async with self.session.get(
                            json.loads(await openai_request.text())['data'][0]['url']
                    ) as image:
                        return await image.content.read()
        except Exception as exc:
            self.loop.create_task(telegram_logging(exc))
            return None

    @async_elapsed_time
    async def edit_image(
            self,
            text: str,
            square_png: bytes
    ) -> T.Optional[bytes]:
        try:
            self.loop.create_task(telegram_logging(f"edit_image prompt: {text}"))

            async with self.semaphore:
                async with self.session.post(
                        "https://api.openai.com/v1/images/edits",
                        headers={
                            "Authorization": f"Bearer {self.api_key}"
                        },
                        data=aiohttp.FormData(
                            (
                                    ("image", square_png),
                                    ("prompt", text),
                                    ("size", "1024x1024"),
                            )
                        )
                ) as openai_request:
                    async with self.session.get(
                            json.loads(await openai_request.text())['data'][0]['url']
                    ) as image:
                        return await image.content.read()
        except Exception as exc:
            self.loop.create_task(telegram_logging(exc))
            return None

    @async_elapsed_time
    async def generate_message(
            self,
            full_text: str,
            short_text="",  # deprecated
            message_username: T.Optional[str] = "",
            chat="ASD",
            only_chatgpt=False,
            only_davinci=False,
            users_opinions: T.Optional[dict] = None,
            moderate=True,
            temperature=1,
            prompt_inject: T.Optional[str] = None,
            return_raw_text: bool = False,
            destroy_message: bool = False,
            remove_words_list=None,
            always_ironic=False,
            mood=0.0,
            replace_pre_prompt: T.Optional[T.List[dict]] = None
    ) -> str:
        short_text = full_text

        datetime_now = datetime.datetime.utcnow() - datetime.timedelta(hours=3)

        full_text = full_text.lower()

        if remove_words_list:
            for word in remove_words_list:
                full_text = full_text.replace(word, '')

        if not message_username:
            message_username = "arrombado"

        if destroy_message:
            model = "text-ada-001"
            prompt = await message_destroyer(full_text)
        else:
            model = await self._model_selector(message_username)
            prompt = (await pre_biased_prompt(
                full_text=full_text,
                last_words=short_text,  # deprecated
                users_opinions=users_opinions
            ) if users_opinions else full_text)

        is_flagged, moderation_results = await self.is_flagged(prompt)

        if is_flagged and moderate:
            prompt = f"reclame com {message_username} porque ele enviou uma mensagem com conteúdo " \
                     f"{' ,'.join([key for key, value in moderation_results['results'][0]['categories'].items() if value])}. " \
                     f"diga que ele poderá ser banido do {chat}."

            only_davinci = True
        else:
            prompt = f"{prompt_inject}\n{prompt}" if prompt_inject else prompt

        timeout = 240

        for i in range(3):
            retry_sleep = int(2 + random.random() * 5)
            try:
                response = await asyncio.wait_for(
                    self._completion(
                        date=datetime_now,
                        prompt=prompt,
                        only_chatgpt=only_chatgpt,
                        only_davinci=only_davinci,
                        temperature=temperature,
                        model=model,
                        always_ironic=always_ironic,
                        mood=mood,
                        biased=users_opinions,
                        replace_pre_prompt=replace_pre_prompt
                    ),
                    timeout=timeout
                )

                if return_raw_text or len(response) < 3:
                    return response

                return await normalize_openai_text(
                    original_message=response,
                    clean_prompts=OPENAI_PROMPTS
                )

            except Exception as exc:
                self.loop.create_task(telegram_logging(exc))
                await asyncio.sleep(retry_sleep)

            timeout /= 2

        return "meu cérebro tá fora do ar"


@async_elapsed_time
async def extract_website_paragraph_content(
        url: str,
        session: aiohttp.ClientSession,
        char_limit=11000
) -> str:
    try:
        if "youtube.com/" in url or "https://youtu.be" in url:
            text = await youtube_caption_extractor(url, char_limit)

        else:
            headers = {"User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) "
                                     "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}
            async with session.get(url, headers=headers) as site:
                text = await html_paragraph_extractor(await site.text(), char_limit)

        if len(text) >= 10:
            return "... responda ou sumarize com base no texto a seguir:\n\n" + text

    except Exception as exc:
        get_running_loop().create_task(telegram_logging(exc))

    return f"essa URL parece inacessível: {url} - opine sobre o que acha que se trata a URL e finalize dizendo que " \
           f"é só sua opinião e que você não conseguiu acessar a URL"


async def return_dall_e_limit(
        id_to_count: int,
        limit_per_user: int,
        dall_uses_list: list
) -> str:
    current = dall_uses_list.count(id_to_count) + 1
    remain = limit_per_user - current
    feedback = ""

    for i in range(current):
        feedback += "❎"

    for i in range(remain):
        feedback += "◻️"

    return feedback


async def list_reducer(l: list) -> list:
    new_list = []
    if len(l) > 30:
        total_size = len(l)
        middle = int(total_size / 2)

        new_list.extend(l[0:6])

        new_list.extend(l[
                        int(middle / 2):int(middle / 2) + 5
                        ])

        new_list.extend(l[middle:middle + 6])

        new_list.extend(l[
                        int(middle / 2 + middle): int(middle / 2 + middle) + 4
                        ])

        new_list.extend(l[total_size - 9:-2])

        return new_list
    return l


def list_crop(l: list, max_size: int) -> list:
    if not len(l):
        return l

    def round_up(n, decimals=0):
        multiplier = 10 ** decimals
        return math.ceil(n * multiplier) / multiplier

    jump = int(round_up(len(l) / max_size))

    new_list = []
    for i in range(jump - 1, len(l), jump):
        new_list.append(l[i])
    return new_list


def chat_log_extractor(
        chats: dict,
        date_now: datetime,
        message_limit: int = 140,
        max_period_days: int = 0,
        chat_id: T.Optional[str] = None,
        stopwords_removal=True,
        remove_accents=True,
        username_last_log: T.Optional[str] = None,
) -> str:
    chats = dict(sorted(chats.items()))

    filtered_chats = defaultdict(list)
    chats_texts = []

    chat_counter = 0

    for key, value in chats.items():
        date = datetime.datetime.strptime(key.split(":")[-1], "%Y-%m-%d")
        dif_days = (date_now - date).days

        if str(chat_id) in key or not chat_id:
            if username_last_log or dif_days <= max_period_days:
                chat_counter += 1

    if chat_counter == 0:
        message_limit_per_chat = int(message_limit / len(chats))
    else:
        message_limit_per_chat = int(message_limit / chat_counter)

    for key, value in chats.items():
        date = datetime.datetime.strptime(key.split(":")[-1], "%Y-%m-%d")
        dif_days = (date_now - date).days
        chat_filtered = []

        if str(chat_id) in key or not chat_id:
            if username_last_log or dif_days <= max_period_days:
                for x in [y for y in value if len(y) > 2]:
                    if x[0].isdigit() and x[2] == ":":
                        chat_filtered.append(x[8:])
                    else:
                        chat_filtered.append(x)
                if not username_last_log:
                    chat_filtered = list_crop(chat_filtered, message_limit_per_chat)

                filtered_chats[key] = [f"\n#conversa de {WEEKDAYS[date.weekday()]} do dia {date.day} de {MONTHS[date.month]}#\n"] + chat_filtered

    for key, value in filtered_chats.items():
        chats_texts = [*chats_texts, *value]

    if username_last_log:
        last_idx = 0
        username_last_log = username_last_log.lower()

        for idx, msg in enumerate(chats_texts[:-3]):
            msg_user = (msg.split(":")[0]).lower()

            if username_last_log in msg_user:
                last_idx = idx

        chats_texts = chats_texts[last_idx:]
        chats_texts = list_crop(chats_texts, message_limit_per_chat)

    text = ("\n".join(chats_texts)).lower() + "."

    if stopwords_removal:
        text = remove_stopwords(text)

    if remove_accents:
        text = unidecode(text)

    if len(text) < 100:
        text = "...não houve uma conversa relevante aqui..."

    return text


@async_elapsed_time
async def chat_log_finder(
        chats: dict,
        date_now: datetime,
        search_msg: str,
        chat_id: T.Optional[str] = None,
        messages_before=2,
        messages_after=8,
        message_limit: int = 140,
        min_threshold=0.8,
        threshold_discount=60,
        max_period_days=14
) -> str:
    chats = dict(sorted(chats.items()))

    message_len = len(search_msg)
    chats_texts = []
    filtered_chat = []
    idx_found = []

    t_discount = len(search_msg) / threshold_discount
    threshold = 1.0 - t_discount
    if threshold < min_threshold:
        threshold = min_threshold

    search_msg = unidecode(search_msg.lower())

    for key, value in chats.items():
        date = datetime.datetime.strptime(key.split(":")[-1], "%Y-%m-%d")
        dif_days = (date_now - date).days
        if str(chat_id) in key:
            if dif_days <= max_period_days:
                for x in [y for y in value if len(y) > 2]:
                    if x[0].isdigit() and x[2] == ":":
                        chats_texts.append(x[8:])
                    else:
                        chats_texts.append(x)

    for i, chat_msg in enumerate(chats_texts):
        username = chat_msg.split(":")[0]
        chat_msg = unidecode((chat_msg.replace(username, "")).lower())

        words = chat_msg.split(" ")

        for word in words:
            ratio = SequenceMatcher(None, search_msg, chat_msg[0:len(search_msg)]).ratio()
            chat_msg = (chat_msg.replace(word, "", 1)).strip()

            if ratio >= threshold:
                idx_found.append(i)
                break

    for i in idx_found:
        try:
            for new_msg in chats_texts[i-messages_before:i+messages_after]:
                if new_msg not in filtered_chat:
                    filtered_chat.append(new_msg)
        except Exception as exc:
            print("sem paciencia de tratar isso ", exc)

    if not len(filtered_chat):
        return "... aparentemente não falaram sobre esse tema ..."

    filtered_chat = list_crop(filtered_chat, message_limit)

    text = ("\n".join(filtered_chat)).lower() + "."

    return text
