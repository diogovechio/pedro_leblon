# Internal
import asyncio
import logging
import os
import sys
from asyncio import AbstractEventLoop
from datetime import datetime
import json
import typing as T

from pedro.brain.modules.agenda import AgendaManager
from pedro.brain.modules.task_list import TaskListManager
# External

# Project
from pedro.__version__ import __version__
from pedro.data_structures.bot_config import BotConfig
from pedro.data_structures.daily_flags import Flags
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.reactions.messages_handler import messages_handler
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.database import Database
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.brain.modules.scheduler import Scheduler

logging.basicConfig(level=logging.INFO)


class TelegramBot:
    """
    Main Telegram bot class that handles configuration, initialization and message processing.

    This class sets up the bot with the provided configuration, manages connections to various
    services like LLM, database, and handles incoming Telegram messages.

    Attributes:
        bot_config_file (str): Path to the bot configuration file
        secrets_file (str): Path to the secrets configuration file  
        debug_mode (bool): Whether to run the bot in debug mode
    """

    def __init__(
            self,
            bot_config_file: str,
            secrets_file: str,
    ):
        """
        Initialize the TelegramBot with configuration files and debug settings.

        Args:
            bot_config_file (str): Path to the bot configuration file
            secrets_file (str): Path to the secrets file containing sensitive data
        """
        self.version = __version__
        self.allowed_list = []

        self.config: BotConfig | None = None
        self.config_file = bot_config_file
        self.secrets_file = secrets_file

        self.llm: LLM | None = None
        self.telegram: Telegram | None = None
        self.database: Database | None = None
        self.user_data: UserDataManager | None = None
        self.chat_history: ChatHistory | None = None
        self.agenda: AgendaManager | None = None
        self.task_list: TaskListManager | None = None
        self.scheduler: Scheduler | None = None

        self.lock = True

        self.flags = Flags(
            swearword_complain_today=False,
            swearword_random_reaction_today=False,
            random_talk_today=False,
            random_tease_message=False
        )

        self.loop: T.Optional[AbstractEventLoop] = None

    async def run(self) -> None:
        """
        Start the bot and begin processing messages.

        This method initializes configuration parameters and starts the main bot tasks.
        Will attempt to reconnect after 60 seconds if an error occurs.
        """
        try:
            self.loop = asyncio.get_running_loop()

            await self.load_config_params()

            await asyncio.gather(
                self._unlocker(),
                self._message_handler()
            )

        except Exception as exc:
            logging.exception(exc)

            await asyncio.sleep(60)

            await self.run()

    async def load_config_params(self) -> None:
        """
        Load and initialize all configuration parameters and services.

        This includes loading bot and secret configurations, initializing database connection,
        telegram client, LLM, chat history manager and scheduler.

        If configuration files don't exist, creates empty templates and exits the bot.
        """
        logging.info(f'Pedro Bot v{__version__} - Loading params')

        # Check if config files exist and create them if they don't
        files_created = False

        if not os.path.exists(self.config_file):
            logging.info(f"Configuration file {self.config_file} not found. Creating empty template.")
            empty_bot_config = {
                "allowed_ids": [],
                "not_internal_chats": []
            }
            with open(self.config_file, 'w', encoding='utf8') as f:
                json.dump(empty_bot_config, f, indent=2)
            files_created = True

        if not os.path.exists(self.secrets_file):
            logging.info(f"Secrets file {self.secrets_file} not found. Creating empty template.")
            empty_secrets = {
                "secrets": {
                    "bot_token": "",
                    "openai_key": "",
                    "open_weather": ""
                }
            }
            with open(self.secrets_file, 'w', encoding='utf8') as f:
                json.dump(empty_secrets, f, indent=2)
            files_created = True

        if files_created:
            logging.info("Empty configuration files have been created. Please fill them with appropriate values and restart the bot.")
            sys.exit(0)

        # Load configuration files
        with open(self.config_file, encoding='utf8') as config_file:
            with open(self.secrets_file) as secret_file:
                bot_config = json.loads(config_file.read())

                bot_config.update(
                    json.loads(secret_file.read())
                )

                self.config: BotConfig = BotConfig(**bot_config)

                self.telegram = Telegram(self.config.secrets.bot_token)
                self.agenda = AgendaManager(self.telegram)
                self.task_list = TaskListManager()
                self.llm = LLM(self.config.secrets.openai_key)
                self.database = Database("database/pedro_database.json")
                self.chat_history = ChatHistory(telegram=self.telegram, llm=self.llm)
                self.user_data = UserDataManager(
                    database=self.database,
                    llm=self.llm,
                    telegram=self.telegram,
                    chat_history=self.chat_history,
                )

                self.scheduler = Scheduler(self.user_data, self.telegram, self.flags)
                self.scheduler.start()

                self.allowed_list = [value.id for value in self.config.allowed_ids]

        logging.info('Loading finished')

    async def _message_handler(self) -> None:
        """
        Main message processing loop that handles incoming Telegram messages.

        Continuously monitors for new messages, adds them to chat history and 
        processes them through the message handler if the bot is unlocked.
        """
        while True:
            try:
                await asyncio.sleep(0.01)

                async for message in self.telegram.get_new_message():
                    message = message.message

                    if message and message.chat:
                        await self.chat_history.add_message(message, chat_id=message.chat.id)
                        self.user_data.add_user_if_not_exists(message)

                        if not self.lock and not self.flags.freeze:
                            self.loop.create_task(
                                messages_handler(
                                    message=message,
                                    telegram=self.telegram,
                                    history=self.chat_history,
                                    user_data=self.user_data,
                                    allowed_list=self.allowed_list,
                                    agenda=self.agenda,
                                    task_list=self.task_list,
                                    llm=self.llm,
                                    flags=self.flags,
                                    config=self.config,
                                )
                            )

            except Exception as exc:
                logging.exception(exc)
                await asyncio.sleep(15)

    async def _unlocker(self) -> None:
        """
        Unlocks the bot after a short delay to avoid reacting with messages sent before the initialization.

        Waits 3 seconds before unlocking the bot to accept and process messages.
        """
        await asyncio.sleep(3)

        self.lock = False
