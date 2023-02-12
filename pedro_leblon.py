import asyncio
import logging
import os
import re
from asyncio import AbstractEventLoop

from datetime import datetime, timedelta
from pathlib import Path

import aiohttp
import json

import face_recognition

import schedule

import typing as T

from aiohttp import ClientSession

from data_classes.bot_config import BotConfig
from data_classes.commemorations import Commemorations
from data_classes.received_message import MessagesResults, TelegramMessage, MessageReceived
from data_structures.max_size_list import MaxSizeList
from messages_reactions import messages_coordinator
from utils.openai_utils import OpenAiCompletion

logging.basicConfig(level=logging.INFO)

session_timeout = aiohttp.ClientTimeout(total=None,sock_connect=120,sock_read=120)

class FakePedro:
    def __init__(
            self,
            bot_config_file: str,
            commemorations_file: str,
            secrets_file: str,
            polling_rate: int = 1,
            debug_mode=False
    ):
        self.allowed_list = []
        self.debug_mode = debug_mode

        self.config: T.Optional[BotConfig] = None
        self.config_file = bot_config_file
        self.commemorations_file = commemorations_file
        self.commemorations: T.Optional[Commemorations] = None
        self.secrets_file = secrets_file

        self.last_id = 0
        self.polling_rate = polling_rate
        self.messages: T.List[T.Any] = []
        self.interacted_updates = MaxSizeList(400)
        self.interacted_messages_with_chat_id = MaxSizeList(400)

        self.messages_in_memory = {}
        self.message_in_memory_min_chars = 15

        self.datetime_now = datetime.now() - timedelta(hours=3)

        self.schedule = schedule

        self.api_route = ""
        self.session: T.Optional[ClientSession] = None

        self.face_images_path = 'faces'
        self.alpha_faces_path = 'faces_alpha'
        self.faces_names = []
        self.faces_files = []
        self.alpha_faces_files = []
        self.face_embeddings = []

        self.used_dall_e_today = []
        self.asked_for_photo = 0
        self.sent_news = 0
        self.sent_games_news = 0
        self.reacted_random_command = 0
        self.roleta_hour = 13
        self.last_roleta_day = 0

        self.mocked_today = False

        self.openai: T.Optional[OpenAiCompletion] = None

        self.loop: T.Optional[AbstractEventLoop] = None

    async def run(self) -> None:
        try:
            from scheduling import scheduler

            Path('tmp').mkdir(exist_ok=True)
            Path('face_lake').mkdir(exist_ok=True)

            self.loop = asyncio.get_running_loop()
            self.session = aiohttp.ClientSession(timeout=session_timeout)

            await self.load_config_params()

            self.loop.create_task(scheduler(self))

            await asyncio.gather(
                self._message_handler(),
                self._message_polling(),
                self._run_scheduler()
            )

        except Exception as exc:
            if isinstance(self.session, ClientSession):
                await self.session.close()
                await asyncio.sleep(0.25)

            logging.exception(exc)

            await asyncio.sleep(60)

            await self.run()

    async def load_config_params(self) -> None:
        logging.info('Loading params')

        with open(self.config_file) as config_file:
            with open(self.secrets_file) as secret_file:
                bot_config = json.loads(config_file.read())

                with open(self.commemorations_file) as comm_file:
                    self.commemorations = Commemorations(json.loads(comm_file.read()))

                bot_config.update(
                    json.loads(secret_file.read())
                )

                self.config = BotConfig(**bot_config)

                self.openai = OpenAiCompletion(
                    api_key=self.config.secrets.openai_key,
                    max_tokens=self.config.openai.max_tokens,
                    max_sentences=self.config.openai.max_sentences,
                    session=self.session,
                    semaphore=self.config.telegram_api_semaphore,
                    davinci_daily_limit=self.config.openai.davinci_daily_limit,
                    curie_daily_limit=self.config.openai.curie_daily_limit,
                    only_ada_users=self.config.openai.ada_only_users,
                    force_model=self.config.openai.force_model
                )

                self.allowed_list = [8375482, -704277411, -884201527, -20341310] if self.debug_mode else [
                    *[value.id for value in self.config.allowed_ids]]
                self.api_route = f"https://api.telegram.org/bot{self.config.secrets.bot_token}"

                self.faces_files = []
                self.alpha_faces_files = []
                self.faces_names = []
                self.face_embeddings = []

                for (_, _, filenames) in os.walk(self.face_images_path):
                    self.faces_files.extend(filenames)
                    break

                for (_, _, filenames) in os.walk(self.alpha_faces_path):
                    self.alpha_faces_files.extend(filenames)
                    break


                for file in self.faces_files:
                    embeddings = face_recognition.face_encodings(
                        face_recognition.load_image_file(f"{self.face_images_path}/{file}")
                    )
                    if len(embeddings):
                        self.faces_names.append(file[:-7])
                        self.face_embeddings.append(embeddings[0])
                        logging.info(f"Loaded embeddings for {file}")
                    else:
                        logging.critical(f'NO EMBEDDINGS FOR {file}')

        logging.info('Loading finished')

    async def _run_scheduler(self) -> None:
        while True:
            try:
                self.schedule.run_pending()
                await asyncio.sleep(self.polling_rate)
                logging.info(f'Scheduler is running. Total jobs: {len(self.schedule.get_jobs())}')
            except Exception as exc:
                logging.exception(exc)
                await asyncio.sleep(15)

    async def _message_polling(self) -> None:
        while True:
            try:
                await asyncio.sleep(self.polling_rate)

                self.datetime_now = datetime.utcnow() - timedelta(hours=3)
                polling_url = f"{self.api_route}/getUpdates?offset={self.last_id}"

                async with self.session.get(polling_url) as request:
                    if 200 <= request.status < 300:
                        response = json.loads((await request.text()).replace('"from":{"', '"from_":{"'))
                        if 'ok' in response and response['ok']:
                            logging.info(f'Message polling task running:'
                                         f"{polling_url.replace(self.config.secrets.bot_token, '#TOKEN#')} last_id: {self.last_id} - {self.datetime_now}")
                            self.messages = MessagesResults(**response)
                            self.last_id = self.messages.result[-1].update_id
            except Exception as exc:
                logging.exception(exc)
                await asyncio.sleep(15)

    async def _message_handler(self) -> None:
        while True:
            try:
                logging.info(f'Message controller task running - {len(self.interacted_updates)} - '
                             f'Next roleta: {self.roleta_hour}')
                if hasattr(self.messages, 'result'):
                    for incoming in (entry for entry in self.messages.result
                                     if entry.update_id not in self.interacted_updates):
                        incoming: MessageReceived
                        self.interacted_updates.append(incoming.update_id)
                        self.interacted_messages_with_chat_id.append(f"{incoming.message.chat.id}:"
                                                                     f"{incoming.message.message_id}")

                        if incoming.message.chat.id not in self.messages_in_memory:
                            self.messages_in_memory[incoming.message.chat.id] = MaxSizeList(75)

                        if incoming.message.text is not None and len(incoming.message.text) > self.message_in_memory_min_chars:
                            self.messages_in_memory[incoming.message.chat.id].append(
                                f"{incoming.message.from_.first_name}: '{incoming.message.text[0:70]}'")

                        logging.info(incoming)

                        if incoming.message is not None:
                            self.loop.create_task(
                                messages_coordinator(self, incoming.message)
                            )

                await asyncio.sleep(self.polling_rate)
            except Exception as exc:
                logging.exception(exc)
                await asyncio.sleep(15)

    async def image_downloader(
            self,
            message: TelegramMessage,
    ) -> T.Optional[bytes]:
        async with self.session.get(
                f"{self.api_route}/getFile?file_id={message.photo[-1].file_id}") as request:
            if 200 <= request.status < 300:
                response = json.loads(await request.text())
                if 'ok' in response and response['ok']:
                    file_path = response['result']['file_path']
                    async with self.session.get(f"{self.api_route.replace('.org/bot', '.org/file/bot')}/"
                                                f"{file_path}") as download_request:
                        if 200 <= download_request.status < 300:
                            return await download_request.read()
                        else:
                            logging.critical(f"Image download failed: {download_request.status}")

    async def send_photo(self, image: bytes, chat_id: int, caption=None, reply_to=None, sleep_time=0, max_retries=5) -> None:
        await asyncio.sleep(sleep_time)

        for _ in range(max_retries):
            try:
                async with asyncio.Semaphore(self.config.telegram_api_semaphore):
                    async with self.session.post(
                            url=f"{self.api_route}/sendPhoto".replace('\n', ''),
                            data=aiohttp.FormData(
                                (
                                        ("chat_id", str(chat_id)),
                                        ("photo", image),
                                        ("reply_to_message_id", str(reply_to) if reply_to else ''),
                                        ('allow_sending_without_reply', 'true'),
                                        ("caption", caption if caption else '')
                                )
                            )
                    ) as resp:
                        logging.info(resp.status)
                        if 200 <= resp.status < 300:
                            break
            except Exception as exc:
                logging.exception(exc)
            await asyncio.sleep(10)

    async def send_video(self, video: bytes, chat_id: int, reply_to=None, sleep_time=0) -> None:
        await asyncio.sleep(sleep_time)

        async with asyncio.Semaphore(self.config.telegram_api_semaphore):
            async with self.session.post(
                    url=f"{self.api_route}/sendVideo".replace('\n', ''),
                    data=aiohttp.FormData(
                        (
                                ("chat_id", str(chat_id)),
                                ("video", video),
                                ("reply_to_message_id", str(reply_to) if reply_to else ''),
                                ('allow_sending_without_reply', 'true'),
                        )
                    )
            ) as resp:
                logging.info(resp.status)

    async def send_action(
            self,
            chat_id: int,
            action=T.Union[T.Literal['typing'], T.Literal['upload_photo'], T.Literal['find_location']]
    ) -> None:
        async with asyncio.Semaphore(self.config.telegram_api_semaphore):
            async with self.session.post(
                    url=f"{self.api_route}/sendChatAction".replace('\n', ''),
                    data=aiohttp.FormData(
                        (
                            ("chat_id", str(chat_id)),
                            ('action', action),
                        )
                    )
            ) as resp:
                logging.info(resp.status)

    async def send_document(self, document: bytes, chat_id: int, caption=None, reply_to=None, sleep_time=0) -> None:
        await asyncio.sleep(sleep_time)

        async with asyncio.Semaphore(self.config.telegram_api_semaphore):
            async with self.session.post(
                    url=f"{self.api_route}/sendDocument".replace('\n', ''),
                    data=aiohttp.FormData(
                        (
                                ("chat_id", str(chat_id)),
                                ("document", document),
                                ("caption", caption if caption else ''),
                                ("reply_to_message_id", str(reply_to) if reply_to else ''),
                                ('allow_sending_without_reply', 'true'),
                        )
                    )
            ) as resp:
                logging.info(resp.status)

    async def forward_message(
            self,
            target_chat_id: int,
            from_chat_id: int,
            message_id: int,
            sleep_time=0,
            replace_token: T.Optional[str] = None
    ) -> int:
        await asyncio.sleep(sleep_time)
        url = self.api_route
        if replace_token:
            url = f"https://api.telegram.org/bot{replace_token}"

        async with asyncio.Semaphore(self.config.telegram_api_semaphore):
            async with self.session.post(
                    url=f"{url}/forwardMessage".replace('\n', ''),
                    data=aiohttp.FormData(
                        (
                            ("chat_id", str(target_chat_id)),
                            ("from_chat_id", str(from_chat_id)),
                            ("message_id", str(message_id)),
                        )
                    )
            ) as resp:
                logging.info(resp.status)

                return resp.status

    async def send_message(
            self,
            message_text: str,
            chat_id: int,
            reply_to=None,
            sleep_time=0,
            parse_mode: str = "Markdown",
            max_retries=7
    ) -> None:
        fallback_parse_modes = ["", "HTML", "MarkdownV2", "Markdown"]

        await asyncio.sleep(sleep_time)

        for i in range(max_retries):
            if i == max_retries - 1:
                message_text = re.sub("[^A-Za-z0-9,.!àèìòùÀÈÌÒÙáéíóúýÁÉÍÓÚÝâêîôûÂÊÎÔÛãñõÃÑÕ]+", " ", message_text)
                if message_text == "":
                    message_text = "tenho nada a te dizer"
            async with asyncio.Semaphore(self.config.telegram_api_semaphore):
                async with self.session.post(
                        f"{self.api_route}/sendMessage".replace('\n', ''),
                        json={
                            "chat_id": chat_id,
                            'reply_to_message_id': reply_to,
                            'allow_sending_without_reply': True,
                            'text': message_text,
                            'parse_mode': parse_mode
                        }
                ) as resp:
                    logging.info(resp.status)
                    if 200 <= resp.status < 300:
                        break
                    parse_mode = fallback_parse_modes.pop() if len(fallback_parse_modes) else ""

    async def leave_chat(self, chat_id: int, sleep_time=0) -> None:
        await asyncio.sleep(sleep_time)

        async with self.session.post(
                f"{self.api_route}/leaveChat".replace('\n', ''),
                json={"chat_id": chat_id}
        ) as resp:
            logging.info(resp.status)


if __name__ == '__main__':
    pedro_leblon = FakePedro(
        bot_config_file='bot_configs.json',
        commemorations_file='commemorations.json',
        secrets_file='secrets.json',
        debug_mode=False
    )

    asyncio.run(
        pedro_leblon.run()
    )
