# Internal
import random

# Project
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.telegram_message import Message
from pedro.utils.prompt_utils import get_photo_description

# Constants
OPENAI_TRASH_LIST = ["pedro:", "pedro", "pedro leblon:", "pedro leblon"]

async def critic_or_praise_reaction(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        llm: LLM,
) -> None:
    if message.text and (
            message.text.startswith("/critique") or
            message.text.startswith("/elogie") or
            message.text.startswith("/simpatize") or
            message.text.startswith("/humilhe")
    ):
        await _critic_or_praise(message, telegram, llm, history)

async def _critic_or_praise(message, telegram, llm, history) -> None:
    with sending_action(chat_id=message.chat.id, telegram=telegram):
        if message.reply_to_message and message.reply_to_message.text:
            text = message.reply_to_message.text
        elif message.reply_to_message and message.reply_to_message.photo:
            text = await get_photo_description(telegram=telegram, llm=llm, message=message.reply_to_message)

        user_name = message.reply_to_message.from_.first_name

        if message.text.startswith("/critique"):
            prompt = f"dê uma bronca em {user_name} por ter dito isso: '{text}'"
        elif message.text.startswith("/elogie"):
            prompt = f"{'elogie o' if round(random.random()) else 'parabenize o'} {user_name} por ter dito isso: " \
                     f"'{text}'"
        elif message.text.startswith("/humilhe"):
            prompt = f"'humilhe o {user_name} por isso: {text}'"
        else:
            prompt = f"simpatize com {user_name} por estar nessa situação: '{text}'"

        reply_to = message.reply_to_message.message_id

        message_text = await llm.generate_text(
            f"{prompt}\npedro:",
            temperature=1,
            model="gpt-3.5-turbo-instruct"
        )
        message_text = message_text.lower()

        if user_name.lower() not in message_text and not message.reply_to_message.from_.is_bot:
            message_text = f"{user_name}, {message_text}"

        if random.random() < 0.25:
            message_text = message_text.upper()

        await telegram.send_message(
            message_text=message_text,
            chat_id=message.chat.id,
            reply_to=reply_to
        )
