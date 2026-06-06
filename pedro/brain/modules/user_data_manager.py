# Internal
import asyncio
import random
import os
import re
from dataclasses import asdict
from typing import List, Optional, Dict
from difflib import SequenceMatcher
import logging

# Project
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.data_structures.user_data import UserData
from pedro.data_structures.telegram_message import Message, From, Chat
from pedro.brain.modules.database import Database
from pedro.utils.text_utils import create_username


class UserDataManager:
    """
    Manages user data, opinions, and sentiment analysis for users interacting with the system.

    This class handles storing and retrieving user information, tracking relationship sentiment,
    analyzing message tone, and managing user opinions based on their interactions.
    """
    def __init__(self, database: Database, llm: LLM, telegram: Telegram, chat_history=None, max_opinions: int = 7):
        """
        Initialize the UserDataManager with necessary dependencies.

        Args:
            database (Database): Database instance for storing and retrieving user data
            llm (LLM): Language model instance for generating text and analyzing messages
            telegram (Telegram): Telegram API interface for sending reactions
            chat_history: Optional chat history manager for accessing historical messages
            max_opinions (int): Maximum number of opinions to store per user (default: 8)
        """
        self.database = database
        self.llm = llm
        self.telegram = telegram
        self.chat_history = chat_history
        self.table_name = "user_data"
        self.max_opinions = max_opinions

        self.sentiment_levels = [
            "Responda de maneira sucinta. Evitando comentários desnecessários.",
            "Seja frio. Responda de acordo com sua opinião sobre o usuário.",
            "Seja impaciente e passivo agressivo. Responda de acordo com sua opinião sobre o usuário. Use o que sabe contra ele."
        ]

        # Start the sentiment decay loop
        asyncio.create_task(self.sentiment_decay_loop())

    def get_sentiment_level_prompt(self, user_id: int) -> str:
        """
        Get the appropriate sentiment level prompt based on the user's relationship sentiment.

        Args:
            user_id (int): The ID of the user to get the sentiment level for

        Returns:
            str: The sentiment level prompt to use when responding to this user
        """
        level = 0
        user_opinion = self.get_user_data(user_id)

        if user_opinion:
            level = round(user_opinion.relationship_sentiment)

            if level > len(self.sentiment_levels) - 1:
                level = len(self.sentiment_levels) - 1
            elif level < 0:
                level = 0

        return self.sentiment_levels[level]

    def get_user_data(self, user_id: int) -> Optional[UserData]:
        """
        Retrieve user data for a specific user ID from the database.

        Args:
            user_id (int): The ID of the user to retrieve data for

        Returns:
            Optional[UserData]: The user data object if found, None otherwise
        """
        results = self.database.search(self.table_name, {"user_id": user_id})
        if results:
            return UserData(**results[0])
        return None

    def get_all_user_opinions(self) -> List[UserData]:
        """
        Retrieve all user data records from the database.

        Returns:
            List[UserData]: A list of UserData objects for all users in the database
        """
        results = self.database.get_all(self.table_name)
        return [UserData(**data) for data in results]

    def get_users(self) -> List[str]:
        """
        Returns a list of usernames from all user opinions.
        If username is None, uses first_name instead.
        Ensures usernames have @ prefix if they don't already.
        """
        all_users = self.get_all_user_opinions()
        users = []

        for user in all_users:
            if user.username:
                username = user.username
                if not username.startswith('@'):
                    username = '@' + username
                users.append(username)
            elif user.first_name:
                users.append(user.first_name)

        return users

    def get_users_by_text_match(self, text: str, threshold: float=0.7) -> List[UserData]:
        """
        Find users whose first name or username matches the given text with a similarity above the threshold.

        Args:
            text (str): The text to match against user names and usernames
            threshold (float, optional): The minimum similarity ratio required for a match. Defaults to 0.8.

        Returns:
            List[UserData]: A list of UserData objects for users that match the text
        """
        all_users = self.get_all_user_opinions()
        matching_users = []

        # Convert text to lowercase for case-insensitive comparison
        text_lower = text.lower()

        for user in all_users:
            # Flag to track if user has been added to matching_users
            user_added = False

            # Check if user has a first_name
            if user.first_name and not user_added:
                first_name_lower = user.first_name.lower()

                for word in text_lower.split():
                    similarity = SequenceMatcher(None, first_name_lower, word).ratio()
                    if similarity >= threshold:
                        matching_users.append(user)
                        user_added = True
                        continue
                    if user_added:
                        break

            # Check if user has a username and hasn't been added yet
            if user.username and not user_added:
                username_lower = user.username.lower()

                for word in text_lower.split():
                    # Direct comparison with the entire text
                    similarity = SequenceMatcher(None, username_lower, word).ratio()
                    if similarity >= threshold:
                        matching_users.append(user)
                        user_added = True
                        continue
                    if user_added:
                        break

        return matching_users

    def adjust_sentiment_by_user_id(self, user_id: int, sentiment_adjust: float) -> Optional[UserData]:
        """
        Adjust the relationship sentiment value for a specific user.

        Args:
            user_id (int): The ID of the user to adjust sentiment for
            sentiment_adjust (float): The amount to adjust the sentiment by (positive or negative)

        Returns:
            Optional[UserData]: The updated user data object if found, None otherwise

        Note:
            The sentiment value will not go below 0.0
        """
        user_opinion = self.get_user_data(user_id)
        if not user_opinion:
            return None

        # Adjust the sentiment
        user_opinion.relationship_sentiment += sentiment_adjust

        if user_opinion.relationship_sentiment < 0.0:
            user_opinion.relationship_sentiment = 0.0

        # Update the user opinion in the database
        self.database.update(
            self.table_name,
            {"relationship_sentiment": user_opinion.relationship_sentiment},
            {"user_id": user_id}
        )

        return user_opinion

    def add_user_if_not_exists(self, message: Message) -> UserData:
        """
        Add a new user to the database if they don't already exist.

        Args:
            message (Message): The message containing user information

        Returns:
            UserData: The existing or newly created user data object
        """
        user_from = message.from_

        existing_user = self.get_user_data(user_from.id)

        if existing_user:
            return existing_user

        user_opinion = UserData(
            user_id=user_from.id,
            username=user_from.username,
            first_name=user_from.first_name,
            last_name=user_from.last_name,
            opinions=[],
            relationship_sentiment=0.0
        )

        self.database.insert(self.table_name, asdict(user_opinion))

        return user_opinion

    async def _check_message_tone(self, text: str, message: Message | None = None) -> (int, str):
        """
        Analyze the tone of a message using the LLM.

        Args:
            text (str): The message text to analyze
            message (Message | None, optional): The original message object. Defaults to None.

        Returns:
            int: A tone code where:
                0 - Apology message
                1 - Loving message
                2 - Friendly message
                3 - Neutral message
                4 - Rude or offensive message

        Note:
            This method may also add an opinion about the user based on the message tone.
        """
        prompt = "Dado a mensagem abaixo:\n" \
                 f"{text}" \
                 f"Responda apenas uma das 6 opções que melhor se adeque ao conteúdo da mensagem:\n" \
                 f"0 - A mensagem é um pedido de desculpas\n" \
                 f"1 - Mensagem amorosa\n" \
                 f"2 - Mensagem amigável\n" \
                 f"3 - Mensagem neutra\n" \
                 f"4 - Mensagem grosseira ou ofensiva\n" \
                 f"Não faça qualquer comentário além de responder um número de 1 a 5."

        response = await self.llm.generate_text(prompt)
        return_num = re.sub(r"\D", "", response)

        if len(return_num):
            if return_num not in [3, 0] and message:
                await self.add_opinion_by_message_tone(text, message=message)

            return int(return_num)

        return 3

    async def _add_opinion(self, prompt: str, message: Message) -> Optional[UserData]:
        """
        Generate an opinion about a user using the LLM and add it to their profile.

        Args:
            prompt (str): The prompt to send to the LLM to generate the opinion
            message (Message): The message containing user information

        Returns:
            Optional[UserData]: The updated user data object if an opinion was added, None otherwise

        Note:
            Will not add the opinion if it contains certain phrases indicating no opinion was formed
        """
        opinion = await self.llm.generate_text(prompt)

        if not any(word.lower() in opinion.lower() for word in ["não tenho", "none", "desculpe,", "por favor,", "entendido,"]):
            return self.add_opinion(opinion=opinion, user_id=message.from_.id)

        return None

    async def _add_opinion_by_historical_messages(self, text: str, message: Message) -> Optional[UserData]:
        """
        Generate an opinion about a user based on their historical messages.

        Args:
            text (str): The concatenated historical messages from the user
            message (Message): The message containing user information

        Returns:
            Optional[UserData]: The updated user data object if an opinion was added, None otherwise
        """
        prompt = (f"Considerando as mensagens:\n\n{text}\n\nEnviadas por "
                  f"{create_username(first_name=message.from_.first_name, username=message.from_.username)} "
                  f"em diversas conversas e em diferentes momentos, resuma de maneira sucinta, em no máximo 8 palavras, "
                  f"o que identificou sobre ele. Caso seja incapaz de gerar alguma observação com base na"
                  f" mensagem fornecida, não peça mais informações, apenas retorne '###NONE###'.")

        return await self._add_opinion(prompt, message)

    async def add_opinion_by_message_tone(self, text: str, message: Message) -> Optional[UserData]:
        """
        Generate an opinion about a user based on the tone of a specific message.

        Args:
            text (str): The message text to analyze
            message (Message): The message containing user information

        Returns:
            Optional[UserData]: The updated user data object if an opinion was added, None otherwise
        """
        prompt = (f"Dada a mensagem '{text}' enviada por "
                  f"{create_username(first_name=message.from_.first_name, username=message.from_.username)}, "
                  f"resuma de maneira sucinta, em no máximo 8 palavras, a sua opinião ou o que identificou sobre ele."
                  f" Caso seja incapaz de gerar alguma opinião ou observação com base na"
                  f" mensagem fornecida, não peça mais informações, apenas retorne '###NONE###'.")

        return await self._add_opinion(prompt, message)

    def add_opinion(self, opinion: str, user_id: int = None, username: str = None) -> Optional[UserData]:
        """
        Add an opinion about a user to their profile.

        Args:
            opinion (str): The opinion to add
            user_id (int, optional): The ID of the user to add the opinion for. Defaults to None.
            username (str, optional): The username of the user to add the opinion for. Defaults to None.

        Returns:
            Optional[UserData]: The updated user data object if the user was found, None otherwise

        Note:
            Either user_id or username must be provided.
            If both are provided, user_id takes precedence.
            Maintains a maximum number of opinions per user by removing the oldest opinion if needed.
        """
        if user_id is None and username is None:
            return None

        user_opinion = None

        if user_id is not None:
            user_opinion = self.get_user_data(user_id)

        if user_opinion is None and username is not None:
            all_users = self.get_all_user_opinions()
            for user in all_users:
                if user.username == username:
                    user_opinion = user
                    break

        if user_opinion is None:
            return None

        user_opinion.opinions.append(opinion)

        if len(user_opinion.opinions) > self.max_opinions:
            user_opinion.opinions.pop(0)

        self.database.update(
            self.table_name,
            {"opinions": user_opinion.opinions},
            {"user_id": user_opinion.user_id}
        )

        return user_opinion

    async def get_opinion_by_historical_messages(self):
        """
        Process historical messages for all users and generate opinions based on their past conversations.

        This method:
        1. Retrieves all users from the database
        2. Collects recent messages (last 2 days) for each user across all chats
        3. Randomly selects up to 10 messages per user
        4. Generates an opinion about each user based on their messages
        5. For users with no recent messages, adds a generic "absent" opinion

        Note:
            Requires chat_history to be available. If not, the method will log a warning and return.
        """
        if not self.chat_history:
            logging.warning("Chat history not available, skipping historical message processing")
            return

        logging.info("Starting to process historical messages for all users")

        # Get all user opinions
        all_users = self.get_all_user_opinions()

        # Get all chat_ids by listing directories in chat_logs_dir
        chat_logs_dir = self.chat_history.chat_logs_dir
        if not os.path.exists(chat_logs_dir):
            logging.warning(f"Chat logs directory {chat_logs_dir} does not exist")
            return

        chat_ids = []
        for item in os.listdir(chat_logs_dir):
            if os.path.isdir(os.path.join(chat_logs_dir, item)):
                try:
                    chat_id = int(item)
                    chat_ids.append(chat_id)
                except ValueError:
                    # Skip directories that are not valid chat_ids
                    pass

        if not chat_ids:
            logging.warning("No chat IDs found in chat logs directory")
            return

        logging.info(f"Found {len(chat_ids)} chat IDs: {chat_ids}")

        for user in all_users:
            user_id = user.user_id
            logging.info(f"Processing historical messages for user {user_id}")

            # Collect messages from all chats
            user_messages = []

            for chat_id in chat_ids:
                # Get messages for this chat for the last 2 days
                try:
                    messages_dict = self.chat_history.get_messages(chat_id=chat_id, days_limit=2)

                    # Filter messages by user_id
                    for date_str, chat_logs in messages_dict.items():
                        for chat_log in chat_logs:
                            if str(chat_log.user_id) == str(user_id):
                                user_messages.append(chat_log)
                except Exception as e:
                    logging.error(f"Error getting messages for chat {chat_id}: {e}")

            # If we have messages for this user
            if user_messages:
                logging.info(f"Found {len(user_messages)} messages for user {user_id} across all chats")

                # Randomly select up to 10 messages
                if len(user_messages) > 30:
                    selected_messages = random.sample(user_messages, 30)
                else:
                    selected_messages = user_messages

                # Make sure we have messages to process
                if selected_messages:
                    # Concatenate all selected messages into a single text
                    concatenated_messages = ""
                    # Use the first message to create the Message object
                    first_chat_log = selected_messages[0]
                    try:
                        # Create a Message object from the first ChatLog
                        from_obj = From(
                            id=int(first_chat_log.user_id),
                            first_name=first_chat_log.first_name,
                            last_name=first_chat_log.last_name,
                            username=first_chat_log.username
                        )

                        message = Message(
                            from_=from_obj,
                            text=""  # Will be set after concatenation
                        )

                        # Concatenate all messages
                        for chat_log in selected_messages:
                            concatenated_messages += f"- {chat_log.message}\n"

                        # Set the concatenated text to the message
                        message.text = concatenated_messages.strip()

                        # Generate a single opinion based on all messages
                        await self._add_opinion_by_historical_messages(concatenated_messages, message)
                    except Exception as e:
                        logging.error(f"Error processing messages for user {user_id}: {e}")
            else:
                self.add_opinion(user_id=user_id, opinion=random.choice(["Sumido.", "Desaparecido.", "Ausente.", "Não presente.", "Inexistente."]))

        logging.info("Finished processing historical messages for all users")

    async def sentiment_decay_loop(self):
        """
        Runs in an infinite loop, decreasing the relationship_sentiment value for each user by 0.2 every 10 minutes,
        until it reaches a minimum of 0.0.
        """
        logging.info("Starting sentiment decay loop")
        while True:
            try:
                # Get all user opinions
                all_users = self.get_all_user_opinions()

                if not all_users:
                    logging.warning("No users found in database for sentiment decay")
                    await asyncio.sleep(60)
                    continue

                logging.info(f"Processing sentiment decay for {len(all_users)} users")

                # For each user with relationship_sentiment > 0.0, decrease it by 0.2
                for user in all_users:
                    if user.relationship_sentiment > 0.0:
                        # Decrease by 0.1, but not below 0.0
                        self.adjust_sentiment_by_user_id(user.user_id, -0.1)
                        logging.info(f"Decreased sentiment for user {user.user_id} by 0.1")

                # Sleep for 60 minutes (3600 seconds)
                await asyncio.sleep(3600)
            except Exception as e:
                logging.error(f"Error in sentiment decay loop: {e}")
                # Sleep for a short time before retrying in case of error
                await asyncio.sleep(60)

    async def adjust_sentiment(self, message: Message) -> (int, str):
        """
        Analyze a message, adjust the user's sentiment based on message tone, and send a reaction.

        Args:
            message (Message): The message to analyze

        Returns:
            tuple: A tuple containing:
                - int: The message tone code (0-4)
                - str: The reaction emoji sent (if any)

        Note:
            Message tone codes:
            0 - Apology message (decreases sentiment significantly)
            1 - Loving message (decreases sentiment moderately)
            2 - Friendly message (decreases sentiment slightly)
            3 - Neutral message (no sentiment change)
            4 - Rude or offensive message (increases sentiment)

            The method will also send an appropriate reaction emoji based on the message tone.
        """
        text = ""
        message_tone = 3
        user_id = message.from_.id

        if message.text:
            text = message.text
        elif message.caption:
            text = message.caption

        if text:
            message_tone = await self._check_message_tone(text, message=message)

        reaction = ""

        if message_tone == 4:
            self.adjust_sentiment_by_user_id(user_id=user_id, sentiment_adjust=4.0)
            reaction = random.choice(["🤬", "😡", "🖕"])
        if message_tone == 2:
            self.adjust_sentiment_by_user_id(user_id=user_id, sentiment_adjust=-0.3)
            reaction = random.choice(["🆒", "🗿"])
        if message_tone == 1:
            self.adjust_sentiment_by_user_id(user_id=user_id, sentiment_adjust=-1.5)
            reaction = random.choice(["❤", "💘", "😘"])

        if message_tone == 0:
            reaction = random.choice(["🤔", "🥴", "🤨", "🙏", "🤷"])

            self.adjust_sentiment_by_user_id(user_id=user_id, sentiment_adjust=-50.0)

        if reaction:
            asyncio.create_task(
                self.telegram.set_message_reaction(
                        message_id=message.message_id,
                        chat_id=message.chat.id,
                        reaction=reaction,
                    )
            )

        return message_tone, reaction
