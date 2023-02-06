import asyncio
import logging
import random
import typing as T

import json
import openai

import aiohttp

from constants.constants import OPENAI_PROMPTS
from utils.text_utils import pre_biased_prompt, message_destroyer, normalize_openai_text, html_paragraph_extractor

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
            max_sentences: int,
            session: aiohttp.ClientSession,
            semaphore: int,
            davinci_daily_limit: int,
            curie_daily_limit: int,
            only_ada_users: T.List[str],
            force_model: T.Optional[str] = None,
    ):
        self.openai_use = 0
        self.dall_e_use = 0
        self.semaphore = semaphore
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.max_sentences = max_sentences
        self.session = session
        self.force_model = force_model
        self.davinci_daily_limit = davinci_daily_limit
        self.curie_daily_limit = curie_daily_limit
        self.ada_only_users = only_ada_users

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

        logging.info(f"Model selected: {model} - OpenAI usage: {self.openai_use}")

        return model

    async def is_flagged(self, text: str) -> T.Tuple[bool, dict]:
        async with asyncio.Semaphore(self.semaphore):
            async with self.session.post(
                "https://api.openai.com/v1/moderations",
                headers=self.headers,
                json={
                    "input": text
                }) as moderation:
                mod = json.loads(await moderation.text())

                return mod['results'][0]['flagged'], mod

    async def _completion(
            self,
            biased: bool,
            mock_message: bool,
            random_model: bool,
            temperature: int = 0,
            message_text: str = "",
            message_username: str = "",
            chat="chat",
            tokens_force: T.Optional[int] = None,
            prompt_inject: T.Optional[str] = None,
            force_model: T.Optional[str] = None
    ) -> str:
        if not message_username:
            message_username = "arrombado"

        model = await self._model_selector(
                            message_username=message_username,
                            mock_message=mock_message,
                            random_model=random_model
                        ) if force_model is None else force_model

        prompt = (await pre_biased_prompt(message_text) if biased else message_text)

        tokens = self.max_tokens if tokens_force is None else tokens_force
        if (
                not tokens_force and self.openai_use >= self.davinci_daily_limit / 4
                and not self.openai_use > self.davinci_daily_limit
        ):
            tokens = round(self.max_tokens / 4)

        if model == "text-davinci-003":
            prompt = prompt[:3500]
        else:
            prompt = prompt[:1600]

        flagged, mod = await self.is_flagged(prompt)

        if flagged:
            prompt = f"do it in brazillian portuguese: complain with @{message_username} for sending a message " \
                     f"with {' ,'.join([key for key, value in mod['results'][0]['categories'].items() if value])} " \
                     f"content. tell him he may be banned from {chat}."
        else:
            prompt = f"{prompt_inject}: {prompt}" if prompt_inject else prompt

        async with asyncio.Semaphore(self.semaphore):
            async with self.session.post(
                    "https://api.openai.com/v1/completions",
                    headers=self.headers,
                    json={
                        "model": model,
                        'prompt': prompt,
                        'max_tokens': tokens,
                        'temperature': temperature,
                        'top_p': 1,
                        'frequency_penalty': 1.0,
                        'presence_penalty': 2.0,
                    }
            ) as openai_request:
                return json.loads(await openai_request.text())['choices'][0]['text']

    async def generate_image(
            self,
            text: str
    ) -> T.Optional[bytes]:
        async with asyncio.Semaphore(self.semaphore):
            async with self.session.post(
                    "https://api.openai.com/v1/images/generations",
                    headers=self.headers,
                    json={'prompt': text,'n': 1, 'size': "256x256"}
            ) as openai_request:
                try:
                    async with self.session.get(
                            json.loads(await openai_request.text())['data'][0]['url']
                    ) as image:
                        self.dall_e_use += 1
                        return await image.content.read()
                except Exception as exc:
                    logging.exception(exc)
                    return None

    async def edit_image(
            self,
            text: str,
            square_png: bytes
    ) -> T.Optional[bytes]:
        #todo: use the fucking api
        logging.info("Blocking the fucking thread with stupid openai lib")
        resp = openai.Image.create_edit(
            image=square_png,
            prompt=text,
            size="256x256",
            n=1,
            api_key=self.api_key,
        )
        try:
            async with self.session.get(resp['data'][0]['url']) as image:
                self.dall_e_use += 1
                logging.info("Thread unblocked")
                return await image.content.read()
        except Exception as exc:
            logging.exception(exc)
            return None

    async def generate_message(
            self,
            message_text: str,
            message_username: T.Optional[str] = "",
            chat="ASD",
            biased=True,
            sentences: T.Optional[int] = None,
            temperature=0,
            tokens: T.Optional[int] = None,
            prompt_inject: T.Optional[str] = None,
            random_model: bool = False,
            mock_message: bool = False,
            return_raw_text: bool = False,
            destroy_message: bool = False,
            remove_words_list=None
    ) -> str:
        if destroy_message:
            force_model = "text-ada-001"
            message_text = await message_destroyer(message_text)
        else:
            force_model = self.force_model

        if not chat:
            chat = "ASD"

        if remove_words_list:
            for word in remove_words_list:
                message_text = message_text.replace(word, '')

        try:
            response = await asyncio.wait_for(
                self._completion(
                    message_username=message_username,
                    chat=chat,
                    biased=biased,
                    mock_message=mock_message,
                    random_model=random_model,
                    force_model=force_model,
                    tokens_force=tokens,
                    prompt_inject=prompt_inject,
                    message_text=message_text,
                    temperature=temperature,
                ),
                timeout=120
            )
        except Exception as exc:
            logging.exception(exc)
            return "meu cérebro tá fora do ar"

        if return_raw_text:
            return response

        return await normalize_openai_text(
            original_message=response,
            sentences=self.max_sentences if sentences is None else sentences,
            clean_prompts=OPENAI_PROMPTS
        )


async def extract_website_paragraph_content(
        url: str,
        session: aiohttp.ClientSession
) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}
        async with session.get(url, headers=headers) as site:
            text = (await html_paragraph_extractor(await site.text()))[:3500]
            if len(text) >= 800 and (200 <= site.status < 300):
                return text
    except Exception as exc:
        logging.exception(exc)

    return f"essa URL parece inacessível: {url} - opine sobre o que acha que se trata a URL e finalize dizendo que é só sua opinião e que você não conseguiu acessar a URL"

async def return_dall_e_limit(_id: int, limit_per_user: int, used_dall_e_today: list) -> str:
    current = used_dall_e_today.count(_id) + 1
    remain = limit_per_user - current
    feedback = ""

    for i in range(current):
        feedback += "❎"

    for i in range(remain):
        feedback += "◻️"

    return feedback
