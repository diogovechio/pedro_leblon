import asyncio
import datetime
import random
import typing as T

import json
from asyncio import get_running_loop

import aiohttp

from constants.constants import OPENAI_PROMPTS, CHATGPT_BS, PEDROS_ROLETAS
from utils.logging_utils import telegram_logging, async_elapsed_time
from utils.text_utils import pre_biased_prompt, message_destroyer, normalize_openai_text, html_paragraph_extractor, \
    youtube_caption_extractor

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
        self.semaphore = semaphore
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
        async with asyncio.Semaphore(self.semaphore):
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
    async def _completion(
            self,
            date: datetime,
            prompt: str,
            model: str = "ada",
            only_chatgpt=False,
            only_davinci=False,
            temperature: int = 0
    ) -> str:
        async with asyncio.Semaphore(self.semaphore):
            if "ada" not in model or only_chatgpt:
                if not only_davinci:
                    self.loop.create_task(telegram_logging(f"Using ChatGPT - OpenAI usage: {self.openai_use}"))

                    async with self.session.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers=self.headers,
                            json={
                                "model": "gpt-3.5-turbo",
                                'messages': [
                                    {"role": "system", "content":
                                        f"Hoje é dia {date.day} do mês {date.month} do ano {date.year}. "
                                        f"São {date.hour} horas e {date.minute} minutos."},
                                    {"role": "assistant", "content":
                                        f"{'Olá. ' if round(random.random()) else 'Fala aí. '}"
                                        f"Meu nome é Pedro. "
                                        f"{'Eu adoro coisas caras e glamourosas. ' if round(random.random()) else 'Adoro conversar sobre jogos. '}"
                                        f"Nasci em Pau Grande, Magé/RJ. "
                                        f"{'Costumo ser quase sempre irônico.' if round(random.random()) else 'Costumo ser um pouco passivo agressivo.' }"
                                        if not only_chatgpt else "Olá! Meu nome é Pedro!"
                                     },
                                    {"role": "user", "content": prompt}
                                ],
                            }
                    ) as chatgpt_request:
                        response = await chatgpt_request.text()
                        response_text = json.loads(response)['choices'][0]['message']['content']

                        self.loop.create_task(telegram_logging(f"ChatGPT: {response_text}"))
                        self.loop.create_task(telegram_logging(prompt))

                        if not any(word in response_text.lower() for word in CHATGPT_BS) or only_chatgpt:
                            return response_text

            self.loop.create_task(telegram_logging(f"{model} - OpenAI usage: {self.openai_use}"))

            async with self.session.post(
                    "https://api.openai.com/v1/completions",
                    headers=self.headers,
                    json={
                        "model": model,
                        'prompt': prompt,
                        'max_tokens': self.max_tokens,
                        'temperature': temperature,
                        'top_p': 1,
                        'frequency_penalty': 1.0,
                        'presence_penalty': 2.0,
                    }
            ) as openai_request:
                response_text = json.loads(await openai_request.text())['choices'][0]['text']
                self.loop.create_task(telegram_logging(prompt))
                self.loop.create_task(telegram_logging(f"{model}: {response_text}"))

                return response_text

    @async_elapsed_time
    async def generate_image(
            self,
            text: str
    ) -> T.Optional[bytes]:
        try:
            self.loop.create_task(telegram_logging(f"generate_image prompt: {text}"))

            async with asyncio.Semaphore(self.semaphore):
                async with self.session.post(
                        "https://api.openai.com/v1/images/generations",
                        headers=self.headers,
                        json={'prompt': text, 'n': 1, 'size': "256x256"}
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

            async with asyncio.Semaphore(self.semaphore):
                async with self.session.post(
                        "https://api.openai.com/v1/images/edits",
                        headers={
                            "Authorization": f"Bearer {self.api_key}"
                        },
                        data=aiohttp.FormData(
                            (
                                    ("image", square_png),
                                    ("prompt", text),
                                    ("size", "256x256"),
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
            short_text="",
            message_username: T.Optional[str] = "",
            chat="ASD",
            only_chatgpt=False,
            only_davinci=False,
            biased=True,
            moderate=True,
            temperature=0,
            prompt_inject: T.Optional[str] = None,
            return_raw_text: bool = False,
            destroy_message: bool = False,
            remove_words_list=None,
            always_ironic=False
    ) -> str:
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
                last_words=short_text,
                always_ironic=always_ironic
            ) if biased else full_text)

        is_flagged, moderation_results = await self.is_flagged(prompt)

        if is_flagged and moderate:
            prompt = f"reclame com {message_username} porque ele enviou uma mensagem com conteúdo " \
                     f"{' ,'.join([key for key, value in moderation_results['results'][0]['categories'].items() if value])}. " \
                     f"diga que ele poderá ser banido do {chat}."
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
                        model=model
                    ),
                    timeout=timeout
                )

                if return_raw_text:
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
            return " em português brasileiro:\n" + text

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
