# Internal
import logging
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import os
from typing import List

# External
import aiohttp

# Project
from pedro.brain.constants.constants import DATE_FULL_FORMAT, DATE_FORMAT
from pedro.brain.modules.datetime_manager import DatetimeManager
from pedro.utils.text_utils import create_username, list_crop, friendly_chat_log
from pedro.data_structures.telegram_message import Message, ReplyToMessage
from pedro.data_structures.chat_log import ChatLog
from pedro.brain.modules.database import Database
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.llm import LLM

"""
Module `chat_history` provides the ChatHistory class to record, store, and retrieve
Telegram conversation logs. It supports processing of text, image, and document messages,
filtering by date or user, and formatting of chat histories for friendly display.
"""

logger = logging.getLogger(__name__)


class ChatHistory:
    """
    A class to manage chat history for Telegram conversations.

    This class handles storing, retrieving and processing chat messages, including
    text messages and images. Messages are stored in JSON files organized by chat ID
    and date.

    Attributes:
        chat_logs_dir (str): Directory path where chat logs are stored
        table_name (str): Name of the database table for chat logs
        datetime (DatetimeManager): Instance of DatetimeManager for date/time operations
        telegram (Telegram): Optional Telegram bot instance for image processing
        llm (LLM): Optional LLM instance for image description generation
        session (aiohttp.ClientSession): HTTP client session

    Args:
        telegram (Telegram, optional): Telegram bot instance. Defaults to None.
        llm (LLM, optional): LLM instance for AI capabilities. Defaults to None.
    """

    def __init__(
            self,
            telegram: Telegram = None,
            llm: LLM = None,
    ):
        self.chat_logs_dir = "database/chat_logs"

        if not os.path.exists(self.chat_logs_dir):
            os.makedirs(self.chat_logs_dir)

        self.table_name = "chat_logs"
        self.datetime = DatetimeManager()
        self.telegram = telegram
        self.llm = llm

        self.session = aiohttp.ClientSession()

    async def _process_image(self, message: Message) -> str:
        """
        Process an image message and generate a short description using LLM.

        Args:
            message (Message): The Telegram message containing an image.

        Returns:
            str: A formatted string containing the image description and caption if present.
                Returns empty string or caption if image processing fails.

        Note:
            Requires telegram and llm attributes to be set.
        """
        if not self.telegram or not self.llm:
            logger.warning("Telegram or LLM not provided, cannot process image")
            return message.text or message.caption or ""

        if not message.photo:
            return message.text or message.caption or ""

        try:
            image = await self.telegram.image_downloader(message)
            if not image:
                logger.warning("Failed to download image")
                return message.text or message.caption or ""

            model = "gpt-4.1-nano"
            prompt = "Faça uma curta descrição da imagem, máximo 10 palavras."
            bot_in_prompt = message.caption and "pedro" in message.caption.lower()

            if bot_in_prompt:
                prompt = f"Descreva a imagem e responda: '{message.caption}'"
                model = "gpt-4.1-mini"

            description = await self.llm.generate_text(prompt=prompt, model=model, image=image)

            if not bot_in_prompt:
                description = (f"{description} "
                               f"[[Caso seja perguntado a Pedro algo sobre a imagem. "
                               f"Peça para sinalizá-la para mais detalhes]]")
                formatted_text = f"[[CURTA DESCRIÇÃO DE IMAGEM ANEXADA: {description} ]]"
            else:
                formatted_text = f"[[IMAGEM ANEXADA: {description} ]]"

            if message.caption:
                formatted_text = f"{message.caption}\n\n{formatted_text}"

            return formatted_text
        except Exception as e:
            logger.exception(f"Error processing image: {e}")
            return message.text or message.caption or ""

    async def _process_document(self, message: Message) -> str:
        """
        Process a document message and format it for storage.

        Args:
            message (Message): The Telegram message containing a document.

        Returns:
            str: A formatted string containing the document information and caption if present.
                Returns empty string or caption if document processing fails.

        Note:
            Requires telegram attribute to be set.
        """
        if not self.telegram:
            logger.warning("Telegram not provided, cannot process document")
            return message.text or message.caption or ""

        if not message.document:
            return message.text or message.caption or ""

        try:
            document = await self.telegram.document_downloader(message)
            if not document:
                logger.warning("Failed to download document")
                return message.text or message.caption or ""

            file_info = f"Nome: {document.file_name}, Tipo: {document.mime_type}"
            formatted_text = f"[[DOCUMENTO ANEXADO: {file_info}]]"

            if message.caption:
                formatted_text = f"{message.caption}\n\n{formatted_text}"

            return formatted_text
        except Exception as e:
            logger.exception(f"Error processing document: {e}")
            return message.text or message.caption or ""

    async def _process_poll(self, message: Message) -> str:
        """
        Process a poll message and format it for storage.

        Args:
            message (Message): The Telegram message containing a poll.

        Returns:
            str: A formatted string containing the poll information.
                Returns empty string if poll processing fails.
        """
        if not message.poll:
            return ""

        try:
            options = "\n".join([f"- {option.text}" for option in message.poll.options])
            formatted_text = f"[[ENQUETE ANEXADA: {message.poll.question}\n{options}]]"

            if message.caption:
                formatted_text = f"{message.caption}\n\n{formatted_text}"

            return formatted_text
        except Exception as e:
            logger.exception(f"Error processing poll: {e}")
            return ""

    async def add_message(self, message: Message | ReplyToMessage | str, chat_id: int, is_pedro: bool = False):
        """
        Adds a message to the chat history database.

        This method processes different types of messages (Message, ReplyToMessage, or str) and stores them in a
        JSON database organized by chat ID and date. It handles user information extraction, image processing if 
        applicable, and database operations.

        Args:
            message (Message | ReplyToMessage | str): The message to store. Can be a Telegram Message object,
                ReplyToMessage object, or a string if the message is from Pedro bot.
            chat_id (int): The ID of the chat where the message was sent.
            is_pedro (bool, optional): Flag indicating if the message is from Pedro bot. Defaults to False.

        Note:
            - Creates chat ID directories and date-based JSON files if they don't exist
            - Processes images if message contains photos and telegram/llm instances are available
            - Stores messages with user information, timestamp and content
            - Handles database operations including insert/update of chat logs
        """
        # Format the date as a string (DD-MM-YYYY)
        date_str = self.datetime.get_current_date_str()

        # Create chat_id directory if it doesn't exist
        chat_id_dir = os.path.join(self.chat_logs_dir, str(chat_id))
        if not os.path.exists(chat_id_dir):
            os.makedirs(chat_id_dir)

        # Create a database file for the current date in the chat_id directory
        db_filename = f"{date_str}.json"
        db_path = os.path.join(chat_id_dir, db_filename)
        db = Database(db_path)

        # Create a ChatLog object based on the message type
        chat_log = None

        message_datetime = self.datetime.now()

        if isinstance(message, Message):
            # Extract user information from TelegramMessage
            user_id = message.from_.id
            username = message.from_.username or create_username(message.from_.first_name, message.from_.last_name)
            first_name = message.from_.first_name or ""
            last_name = message.from_.last_name or ""

            # Check if message has a photo or document and process it
            if message.photo and self.telegram and self.llm:
                message_text = await self._process_image(message)
            elif message.document and self.telegram:
                message_text = await self._process_document(message)
            elif message.poll:
                message_text = await self._process_poll(message)
            else:
                message_text = message.text or message.caption or ""

            chat_log = ChatLog(
                user_id=str(user_id),
                username=username,
                first_name=first_name,
                last_name=last_name,
                datetime=str(message_datetime),
                message=message_text
            )

        elif isinstance(message, ReplyToMessage):
            # Extract user information from ReplyToMessage
            user_id = message.from_.id if message.from_ else 0
            username = message.from_.username or create_username(message.from_.first_name,
                                                                 message.from_.last_name) if message.from_ else ""
            first_name = message.from_.first_name or "" if message.from_ else ""
            last_name = message.from_.last_name or "" if message.from_ else ""
            message_text = message.text or ""

            chat_log = ChatLog(
                user_id=str(user_id),
                username=username,
                first_name=first_name,
                last_name=last_name,
                datetime=str(message_datetime),
                message=message_text
            )

        elif isinstance(message, str) and is_pedro:
            user_id = 0
            username = "pedroleblonbot"
            first_name = "Pedro"
            last_name = "Leblon"
            message_text = message
            message_datetime = self.datetime.now()

            chat_log = ChatLog(
                user_id=str(user_id),
                username=username,
                first_name=first_name,
                last_name=last_name,
                datetime=str(message_datetime),
                message=message_text
            )

        if chat_log:
            # Convert ChatLog to dictionary
            chat_log_dict = asdict(chat_log)

            # Check if there's already an entry for this chat_id
            results = db.search(self.table_name, {"chat_id": chat_id})

            if results:
                # Entry exists, update it
                chat_data = results[0]

                # Append to existing logs
                if "logs" in chat_data:
                    chat_data["logs"].append(chat_log_dict)
                else:
                    chat_data["logs"] = [chat_log_dict]

                # Update the database
                db.update(self.table_name, chat_data, {"chat_id": chat_id})
            else:
                # Create new entry
                chat_data = {
                    "chat_id": chat_id,
                    "logs": [chat_log_dict]
                }

                # Insert into database
                db.insert(self.table_name, chat_data)

            # Close the database connection
            db.close()
    def get_messages(self, chat_id: int, days_limit: int=0, max_messages: int=0) -> dict[str, list[ChatLog]]:
        """
        Retrieve chat logs for a specific chat, optionally filtering by date range and message count.

        Args:
            chat_id (int): ID of the Telegram chat.
            days_limit (int, optional): Number of days back to include messages. Defaults to 0 (no limit).
            max_messages (int, optional): Maximum number of messages to return. Defaults to 0 (no limit).

        Returns:
            dict[str, list[ChatLog]]: Mapping of date strings (formatted with DATE_FULL_FORMAT)
            to lists of ChatLog entries for that date.
        """
        # Get the current date
        current_date = self.datetime.now()

        # Determine the date range to search
        if days_limit > 0:
            start_date = current_date - timedelta(days=days_limit)
        else:
            # If no limit is specified, use a very old date to include all files
            start_date = datetime(1970, 1, 1)

        # Add timezone information to start_date (UTC-3)
        start_date = start_date.replace(tzinfo=timezone(timedelta(hours=-3)))

        # List all JSON files in the chat_id directory
        result = dict()

        # Check if the chat_id directory exists
        chat_id_dir = os.path.join(self.chat_logs_dir, str(chat_id))
        if not os.path.exists(chat_id_dir):
            return result

        # Get all JSON files and sort them by date (oldest to newest)
        json_files = [f for f in os.listdir(chat_id_dir) if f.endswith('.json')]
        json_files.sort(key=lambda x: datetime.strptime(x[:-5], DATE_FORMAT))

        for filename in json_files:
            try:
                # Parse the date from the filename
                date_str = filename[:-5]  # Remove .json extension
                date_obj = datetime.strptime(date_str, DATE_FORMAT).replace(tzinfo=timezone(timedelta(hours=-3)))

                # Check if the date is within the range
                if date_obj >= start_date:
                    # Create a database object for this file
                    db_path = os.path.join(chat_id_dir, filename)
                    db = Database(db_path)

                    # Search for messages
                    chat_results = db.search(self.table_name, {"chat_id": chat_id})

                    if chat_results:
                        chat_data = chat_results[0]

                        # Extract logs
                        if "logs" in chat_data:
                            logs = chat_data["logs"]

                            # Convert logs to ChatLog objects
                            chat_logs = []
                            for log_dict in logs:
                                # Convert datetime string to datetime object if it's a string
                                dt = log_dict["datetime"]

                                chat_log = ChatLog(
                                    user_id=log_dict["user_id"],
                                    username=log_dict["username"],
                                    first_name=log_dict["first_name"],
                                    last_name=log_dict["last_name"],
                                    datetime=dt,
                                    message=log_dict["message"]
                                )
                                chat_logs.append(chat_log)

                            if chat_logs:
                                chat_logs.sort(key=lambda log: datetime.strptime(log.datetime, DATE_FULL_FORMAT))
                                result[date_str] = chat_logs

                    db.close()

            except Exception as exc:
                logger.exception(f"Error parsing date from filename: {filename} - {exc}")
                continue

        if max_messages and result:
            # Count total messages across all lists
            total_messages = sum(len(messages) for messages in result.values())

            # If we have more messages than the limit
            if total_messages > max_messages:
                # Calculate how many messages to keep per list
                num_lists = len(result)

                # If we have more lists than max_messages, ensure at least 1 message per list
                if num_lists > max_messages:
                    messages_per_list = 1
                else:
                    # Otherwise distribute evenly, with a minimum of 1 per list
                    messages_per_list = max(1, max_messages // num_lists)

                # Apply list_crop to each list in the dictionary
                for date_str in result:
                    # Adjust messages_per_list if we have fewer messages than calculated
                    actual_messages = min(messages_per_list, len(result[date_str]))
                    result[date_str] = list_crop(result[date_str], actual_messages)

        return result

    def get_last_messages(self, chat_id: int, limit: int = 20, days: int=0) -> List[ChatLog]:
        """
        Get the most recent messages from a chat.

        Args:
            chat_id (int): ID of the Telegram chat.
            limit (int, optional): Maximum number of messages to return. Defaults to 20.
            days (int, optional): Number of days back to include messages. Defaults to 0 (no limit).

        Returns:
            List[ChatLog]: List of the most recent ChatLog entries.
        """
        # Get messages using the existing method
        messages_dict = self.get_messages(chat_id, days)

        # Flatten the dictionary into a single list
        all_messages = []
        for date_str, chat_logs in messages_dict.items():
            all_messages.extend(chat_logs)

        # Return only the last X messages
        if len(all_messages) > limit:
            return all_messages[-limit:]
        return all_messages

    def get_friendly_last_messages(self, chat_id: int, limit: int = 20, days: int=0) -> str:
        """
        Get a human-friendly string representation of the most recent messages.

        Args:
            chat_id (int): ID of the Telegram chat.
            limit (int, optional): Maximum number of messages to include. Defaults to 20.
            days (int, optional): Number of days back to include messages. Defaults to 0 (no limit).

        Returns:
            str: Friendly-formatted chat log.
        """
        return friendly_chat_log(self.get_last_messages(chat_id, limit, days))

    def get_messages_since_last_from_user(self, chat_id: int, user_id: int, tolerance: int=5) -> List[ChatLog]:
        """
        Retrieve messages from a chat since the last message sent by a given user.

        Args:
            chat_id (int): ID of the Telegram chat.
            user_id (int): ID of the user whose last message is the reference point.
            tolerance (int, optional): Minimum number of intervening messages to skip
                before considering a previous user message. Defaults to 5.

        Returns:
            List[ChatLog]: List of ChatLog entries after the identified user message.
            If no user message is found within the tolerance, returns all available messages.
        """
        # Get all messages for this chat
        messages_dict = self.get_messages(chat_id, 10)

        # Flatten the dictionary into a single list
        all_messages = []
        for date_str, chat_logs in messages_dict.items():
            all_messages.extend(chat_logs)

        # Sort messages by datetime
        all_messages.sort(key=lambda log: datetime.strptime(log.datetime, DATE_FULL_FORMAT))

        # Find the index of the last message from the specified user
        last_user_msg_index = -1
        for i in range(len(all_messages) - 1, -1, -1):
            if all_messages[i].user_id == str(user_id):
                last_user_msg_index = i
                break

        # If no message from the user was found, return all messages
        if last_user_msg_index == -1:
            return all_messages

        # Add tolerance of 5 messages to find a previous message from the user
        # This prevents returning only the current message when a user asks for messages since their last message
        previous_user_msg_index = -1

        # Start searching from the last message index, skipping at least 'tolerance' messages
        for i in range(last_user_msg_index - 1, -1, -1):
            if all_messages[i].user_id == str(user_id) and (last_user_msg_index - i) > tolerance:
                previous_user_msg_index = i
                break

        # If a previous message with sufficient tolerance was found, use that as the starting point
        if previous_user_msg_index != -1:
            return all_messages[previous_user_msg_index:-1]

        # Otherwise, return all messages after the last message from the user
        return all_messages[last_user_msg_index:-1]

    def get_friendly_messages_since_last_from_user(self, chat_id: int, user_id: int) -> str:
        """
        Get a human-friendly string of messages since the last message from a specific user.

        Args:
            chat_id (int): ID of the Telegram chat.
            user_id (int): ID of the user whose last message is the reference point.

        Returns:
            str: Friendly-formatted subset of chat logs.
        """
        chat_cropped = list_crop(self.get_messages_since_last_from_user(chat_id, user_id), max_size=40)

        return friendly_chat_log(chat_cropped)
