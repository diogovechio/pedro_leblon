"""
Telegram module for handling communication with the Telegram Bot API.

This module provides a class for interacting with the Telegram Bot API,
including methods for sending and receiving messages, media, and other
Telegram-specific actions.
"""

# Internal
import asyncio
import logging
import typing as T
import json
import sys
import random

# External
import aiohttp


# Project
from pedro.data_structures.telegram_message import Message, MessagesResults, MessageReceived
from pedro.data_structures.max_size_list import MaxSizeList
from pedro.data_structures.images import MessageImage, MessageDocument


class Telegram:
    """
    A class for interacting with the Telegram Bot API.

    This class provides methods for sending messages, media, and performing
    various actions through the Telegram Bot API. It also handles message
    polling to receive new messages.
    """
    def __init__(
        self,
        token: str,
        semaphore: int = 3,
        polling_rate: int = 0.5
    ):
        """
        Initialize the Telegram client.

        Args:
            token (str): The Telegram Bot API token.
            semaphore (int, optional): Maximum number of concurrent API requests. Defaults to 3.
            polling_rate (int, optional): Rate at which to poll for new messages in seconds. Defaults to 0.5.
        """
        self._api_route = f"https://api.telegram.org/bot{token}"
        self._semaphore = asyncio.Semaphore(semaphore)
        self._polling_rate = polling_rate

        self._last_id = 0
        self._messages = MessagesResults()
        self._interacted_updates = MaxSizeList(50)

        self._session = aiohttp.ClientSession()

        asyncio.create_task(self._message_polling())

    async def get_new_message(self) -> T.AsyncGenerator[MessageReceived, None]:
        """
        Get new messages from Telegram.

        Yields:
            MessageReceived: New messages that haven't been processed yet.

        Returns:
            AsyncGenerator[MessageReceived, None]: An async generator of new messages.
        """
        if self._messages.result:
            for message in self._messages.result:
                message: MessageReceived

                if message.update_id not in self._interacted_updates:
                    yield message

                    self._interacted_updates.append(message.update_id)

    async def _message_polling(self) -> None:
        """
        Internal method to continuously poll for new messages from Telegram.

        This method runs as a background task and updates the internal message store
        with new messages from the Telegram API.
        """
        while True:
            try:
                await asyncio.sleep(self._polling_rate)

                polling_url = f"{self._api_route}/getUpdates?offset={self._last_id}"

                async with self._session.get(polling_url) as request:
                    if 200 <= request.status < 300:
                        response = json.loads((await request.text()).replace('"from":{"', '"from_":{"'))
                        if 'ok' in response and response['ok']:
                            self._messages = MessagesResults(**response)
                            if self._messages.result:
                                self._last_id = self._messages.result[-1].update_id
            except Exception as exc:
                logging.exception(exc)
                await asyncio.sleep(15)

    async def image_downloader(
            self,
            message: Message,
    ) -> None | MessageImage:
        """
        Download an image from a Telegram message.

        This method attempts to download an image from a message, either from
        the photo field or from a document if it's an image file.

        Args:
            message (Message): The Telegram message containing the image.

        Returns:
            MessageImage or None: The downloaded image data or None if download failed.
        """
        if not message.photo and message.document:
            document = await self.document_downloader(message)

            if document and document.mime_type in ["image/jpeg", "image/png"]:
                return MessageImage(
                    url=document.url,
                    bytes=document.bytes,
                    from_doc=True
                )
            else:
                return None

        async with self._session.get(
                f"{self._api_route}/getFile?file_id={message.photo[-1].file_id}") as request:
            if 200 <= request.status < 300:
                response = json.loads(await request.text())
                if 'ok' in response and response['ok']:
                    file_path = response['result']['file_path']
                    url = f"{self._api_route.replace('.org/bot', '.org/file/bot')}/{file_path}"
                    async with self._session.get(url) as download_request:
                        if 200 <= download_request.status < 300:
                            return MessageImage(
                                url=url,
                                bytes=await download_request.read()
                            )
                        else:
                            logging.critical(f"Image download failed: {download_request.status}")

    async def document_downloader(
            self,
            message: Message,
            limit_mb: int = 10,
    ) -> None | MessageDocument:
        """
        Download a document from a Telegram message.

        This method downloads a document from a message if it exists and is within
        the specified size limit.

        Args:
            message (Message): The Telegram message containing the document.
            limit_mb (int, optional): Maximum document size in megabytes. Defaults to 10.

        Returns:
            MessageDocument or None: The downloaded document data or None if download failed
                                    or document exceeds size limit.
        """
        if not message.document or message.document.file_size > limit_mb * 1024 * 1024:
            return None

        async with self._session.get(
                f"{self._api_route}/getFile?file_id={message.document.file_id}") as request:
            if 200 <= request.status < 300:
                response = json.loads(await request.text())
                if 'ok' in response and response['ok']:
                    file_path = response['result']['file_path']
                    url = f"{self._api_route.replace('.org/bot', '.org/file/bot')}/{file_path}"
                    async with self._session.get(url) as download_request:
                        if 200 <= download_request.status < 300:
                            return MessageDocument(
                                url=url,
                                bytes=await download_request.read(),
                                file_name=message.document.file_name or "document",
                                mime_type=message.document.mime_type or "application/octet-stream"
                            )
                        else:
                            logging.critical(f"Document download failed: {download_request.status}")

    async def send_photo(self, image: bytes, chat_id: int, caption=None, reply_to=None, sleep_time=0, max_retries=5) -> None:
        """
        Send a photo to a Telegram chat.

        Args:
            image (bytes): The image data to send.
            chat_id (int): The ID of the chat to send the photo to.
            caption (str, optional): Caption for the photo. Defaults to None.
            reply_to (int, optional): Message ID to reply to. Defaults to None.
            sleep_time (int, optional): Time to sleep before sending in seconds. Defaults to 0.
            max_retries (int, optional): Maximum number of retry attempts. Defaults to 5.
        """
        await asyncio.sleep(sleep_time)

        for _ in range(max_retries):
            async with self._semaphore:
                async with self._session.post(
                        url=f"{self._api_route}/sendPhoto".replace('\n', ''),
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
                    logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")
                    if 200 <= resp.status < 300:
                        break
            await asyncio.sleep(10)

    async def send_video(self, video: bytes, chat_id: int, reply_to=None, sleep_time=0) -> None:
        """
        Send a video to a Telegram chat.

        Args:
            video (bytes): The video data to send.
            chat_id (int): The ID of the chat to send the video to.
            reply_to (int, optional): Message ID to reply to. Defaults to None.
            sleep_time (int, optional): Time to sleep before sending in seconds. Defaults to 0.
        """
        await asyncio.sleep(sleep_time)

        async with self._semaphore:
            async with self._session.post(
                    url=f"{self._api_route}/sendVideo".replace('\n', ''),
                    data=aiohttp.FormData(
                        (
                                ("chat_id", str(chat_id)),
                                ("video", video),
                                ("reply_to_message_id", str(reply_to) if reply_to else ''),
                                ('allow_sending_without_reply', 'true'),
                        )
                    )
            ) as resp:
                logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")

    async def send_voice(self, audio: bytes, chat_id: int, reply_to=None, sleep_time=0) -> None:
        """
        Send a voice message to a Telegram chat.

        Args:
            audio (bytes): The audio data to send as voice message.
            chat_id (int): The ID of the chat to send the voice message to.
            reply_to (int, optional): Message ID to reply to. Defaults to None.
            sleep_time (int, optional): Time to sleep before sending in seconds. Defaults to 0.
        """
        await asyncio.sleep(sleep_time)

        async with self._semaphore:
            async with self._session.post(
                    url=f"{self._api_route}/sendVoice".replace('\n', ''),
                    data=aiohttp.FormData(
                        (
                                ("chat_id", str(chat_id)),
                                ("voice", audio),
                                ("reply_to_message_id", str(reply_to) if reply_to else ''),
                                ('allow_sending_without_reply', 'true'),
                        )
                    )
            ) as resp:
                logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")

    async def send_action(
            self,
            chat_id: int,
            action: T.Union[T.Literal['typing'], T.Literal['upload_photo'], T.Literal['find_location']] = 'typing',
            repeats=False
    ) -> None:
        """
        Send a chat action to a Telegram chat.

        This method sends a chat action (such as "typing...") to indicate that
        the bot is performing some action.

        Args:
            chat_id (int): The ID of the chat to send the action to.
            action (Union[Literal['typing'], Literal['upload_photo'], Literal['find_location']], optional): 
                The action to send. Defaults to 'typing'.
            repeats (bool, optional): Whether to repeat the action continuously. Defaults to False.
        """
        while True:
            async with self._semaphore:
                async with self._session.post(
                        url=f"{self._api_route}/sendChatAction".replace('\n', ''),
                        data=aiohttp.FormData(
                            (
                                ("chat_id", str(chat_id)),
                                ('action', action),
                            )
                        )
                ) as resp:
                    logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")

            if not repeats:
                break

            await asyncio.sleep(round(5 + (random.random() * 2)))

    async def send_document(self, document: bytes, chat_id: int, caption=None, reply_to=None, sleep_time=0, file_name=None) -> None:
        """
        Send a document to a Telegram chat.

        Args:
            document (bytes): The document data to send.
            chat_id (int): The ID of the chat to send the document to.
            caption (str, optional): Caption for the document. Defaults to None.
            reply_to (int, optional): Message ID to reply to. Defaults to None.
            sleep_time (int, optional): Time to sleep before sending in seconds. Defaults to 0.
            file_name (str, optional): Name and extension for the document file. Defaults to None.
        """
        await asyncio.sleep(sleep_time)

        form_data = aiohttp.FormData()
        form_data.add_field("chat_id", str(chat_id))

        # Add document with filename if provided
        if file_name:
            form_data.add_field("document", document, filename=file_name)
        else:
            form_data.add_field("document", document)

        form_data.add_field("caption", caption if caption else '')
        form_data.add_field("reply_to_message_id", str(reply_to) if reply_to else '')
        form_data.add_field('allow_sending_without_reply', 'true')

        async with self._semaphore:
            async with self._session.post(
                    url=f"{self._api_route}/sendDocument".replace('\n', ''),
                    data=form_data
            ) as resp:
                logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")

    async def forward_message(
            self,
            target_chat_id: int,
            from_chat_id: int,
            message_id: int,
            sleep_time=0,
            replace_token: T.Optional[str] = None
    ) -> int:
        """
        Forward a message from one chat to another.

        Args:
            target_chat_id (int): The ID of the chat to forward the message to.
            from_chat_id (int): The ID of the chat to forward the message from.
            message_id (int): The ID of the message to forward.
            sleep_time (int, optional): Time to sleep before forwarding in seconds. Defaults to 0.
            replace_token (Optional[str], optional): Alternative bot token to use. Defaults to None.

        Returns:
            int: HTTP status code of the request.
        """
        await asyncio.sleep(sleep_time)
        url = self._api_route
        if replace_token:
            url = f"https://api.telegram.org/bot{replace_token}"

        async with self._semaphore:
            async with self._session.post(
                    url=f"{url}/forwardMessage".replace('\n', ''),
                    data=aiohttp.FormData(
                        (
                            ("chat_id", str(target_chat_id)),
                            ("from_chat_id", str(from_chat_id)),
                            ("message_id", str(message_id)),
                        )
                    )
            ) as resp:
                logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")

                return resp.status

    async def send_message(
            self,
            message_text: str,
            chat_id: int,
            reply_to=None,
            sleep_time=0,
            parse_mode: str = "Markdown",
            disable_notification=False,
            disable_web_page_preview=False,
            max_retries=7
    ) -> T.Optional[int]:
        """
        Send a text message to a Telegram chat.

        This method attempts to send a message with the specified parse mode,
        falling back to other parse modes if the initial attempt fails.

        Args:
            message_text (str): The text message to send.
            chat_id (int): The ID of the chat to send the message to.
            reply_to (int, optional): Message ID to reply to. Defaults to None.
            sleep_time (int, optional): Time to sleep before sending in seconds. Defaults to 0.
            parse_mode (str, optional): Message formatting mode. Defaults to "Markdown".
            disable_notification (bool, optional): Whether to send the message silently. Defaults to False.
            disable_web_page_preview (bool, optional): Whether to disable link previews. Defaults to False.
            max_retries (int, optional): Maximum number of retry attempts. Defaults to 7.

        Returns:
            Optional[int]: The message_id of the sent message, or None if sending failed.
        """
        fallback_parse_modes = ["", "HTML", "MarkdownV2", "Markdown"]

        await asyncio.sleep(sleep_time)

        for i in range(max_retries):
            async with self._semaphore:
                async with self._session.post(
                        f"{self._api_route}/sendMessage".replace('\n', ''),
                        json={
                            "chat_id": chat_id,
                            'reply_to_message_id': reply_to,
                            'allow_sending_without_reply': True,
                            'text': message_text,
                            'disable_notification': disable_notification,
                            'disable_web_page_preview': disable_web_page_preview,
                            'parse_mode': parse_mode
                        }
                ) as resp:
                    logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")

                    if 200 <= resp.status < 300:
                        try:
                            response_data = await resp.json()
                            return response_data.get('result', {}).get('message_id')
                        except Exception:
                            return None
                    parse_mode = fallback_parse_modes.pop() if len(fallback_parse_modes) else ""

        return None

    async def leave_chat(self, chat_id: int, sleep_time=0) -> None:
        """
        Leave a Telegram chat.

        Args:
            chat_id (int): The ID of the chat to leave.
            sleep_time (int, optional): Time to sleep before leaving in seconds. Defaults to 0.
        """
        await asyncio.sleep(sleep_time)

        async with self._session.post(
                f"{self._api_route}/leaveChat".replace('\n', ''),
                json={"chat_id": chat_id}
        ) as resp:
            logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")

    async def delete_message(self, chat_id: int, message_id: int) -> None:
        """
        Delete a message from a Telegram chat.

        Args:
            chat_id (int): The ID of the chat containing the message.
            message_id (int): The ID of the message to delete.
        """
        async with self._session.post(
                f"{self._api_route}/deleteMessage".replace('\n', ''),
                json={
                    "chat_id": chat_id,
                    "message_id": message_id
                }
        ) as resp:
            logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")

    async def edit_message(
            self,
            message_text: str,
            chat_id: int,
            message_id: int,
            parse_mode: str = "Markdown",
            disable_web_page_preview: bool = False,
            max_retries: int = 7
    ) -> bool:
        """
        Edit an existing text message in a Telegram chat.

        This method attempts to edit a message with the specified parse mode,
        falling back to other parse modes if the initial attempt fails.

        Args:
            message_text (str): New text for the message.
            chat_id (int): The ID of the chat containing the message.
            message_id (int): The ID of the message to edit.
            parse_mode (str, optional): Message formatting mode. Defaults to "Markdown".
            disable_web_page_preview (bool, optional): Disable link previews. Defaults to False.
            max_retries (int, optional): Maximum retry attempts. Defaults to 7.

        Returns:
            bool: True if edit was successful, False otherwise.
        """
        fallback_parse_modes = ["", "HTML", "MarkdownV2", "Markdown"]

        for i in range(max_retries):
            async with self._semaphore:
                async with self._session.post(
                        f"{self._api_route}/editMessageText".replace('\n', ''),
                        json={
                            "chat_id": chat_id,
                            "message_id": message_id,
                            "text": message_text,
                            "disable_web_page_preview": disable_web_page_preview,
                            "parse_mode": parse_mode
                        }
                ) as resp:
                    logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")

                    if 200 <= resp.status < 300:
                        return True
                    parse_mode = fallback_parse_modes.pop() if len(fallback_parse_modes) else ""

        return False

    async def set_chat_title(self, chat_id: int, title: str) -> None:
        """
        Set the title of a Telegram chat.

        Args:
            chat_id (int): The ID of the chat to rename.
            title (str): The new title for the chat.
        """
        async with self._session.post(
                f"{self._api_route}/setChatTitle".replace('\n', ''),
                json={
                    "chat_id": chat_id,
                    "title": title
                }
        ) as resp:
            logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")

    async def set_message_reaction(
            self,
            message_id: int,
            chat_id: int,
            reaction=None,
            sleep_time=0,
            is_big=True
    ) -> None:
        """
        Add an emoji reaction to a message.

        Args:
            message_id (int): The ID of the message to react to.
            chat_id (int): The ID of the chat containing the message.
            reaction (str, optional): The emoji to use as reaction. Defaults to None.
            sleep_time (int, optional): Time to sleep before reacting in seconds. Defaults to 0.
            is_big (bool, optional): Whether to show the reaction as big. Defaults to True.
        """
        await asyncio.sleep(sleep_time)

        async with self._session.post(
                url=f"{self._api_route}/setMessageReaction".replace('\n', ''),
                json={
                        "chat_id": str(chat_id),
                        "message_id": message_id,
                        "reaction": [{"type": "emoji", "emoji": reaction}],
                        "is_big": is_big
                    }
        ) as resp:
            logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")
