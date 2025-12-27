# Internal
import logging
import random
import asyncio

from pedro.brain.modules.task_list import TaskListManager
# Project
from pedro.brain.reactions.agent_common import run_agent_reaction
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.bot_config import BotConfig
from pedro.data_structures.daily_flags import Flags
from pedro.data_structures.telegram_message import Message
from pedro.utils.prompt_utils import text_trigger, random_trigger, create_self_complement_prompt, check_web_search
from pedro.utils.text_utils import adjust_pedro_casing

logger = logging.getLogger(__name__)

async def pedro_reaction(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        llm: LLM,
        config: BotConfig,
        daily_flags: Flags,
        task_list: TaskListManager,
) -> None:
    """
    Handle messages using the autonomous Agent, replacing the old default reaction.
    """
    _text_trigger = text_trigger(message=message)
    _random_trigger = random_trigger(message=message, daily_flags=daily_flags)

    if not (_text_trigger or _random_trigger):
        return

    # Trigger action typing
    await user_data.adjust_sentiment(message)
    
    with sending_action(chat_id=message.chat.id, telegram=telegram, user=message.from_.username if _text_trigger else None):
        await run_agent_reaction(
            message=message,
            history=history,
            telegram=telegram,
            user_data=user_data,
            llm=llm,
            config=config,
            task_list=task_list
        )

    # 8. Randomly keep reacting
    await _randomly_keeps_reacting(
        message=message,
        history=history,
        telegram=telegram,
        user_data=user_data,
        llm=llm,
    )

async def _randomly_keeps_reacting(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        llm: LLM
):
    if random.random() > 0.15:
        return

    with sending_action(chat_id=message.chat.id, telegram=telegram):
        prompt = await create_self_complement_prompt(
            history=history,
            chat_id=message.chat.id,
            telegram=telegram,
            llm=llm,
            user_data=user_data
        )

        response = await adjust_pedro_casing(
            await llm.generate_text(prompt)
        )

        await history.add_message(response, chat_id=message.chat.id, is_pedro=True)

        if "agressivo" in prompt.lower():
            response = response.upper()

        await telegram.send_message(
            message_text=response,
            chat_id=message.chat.id,
            sleep_time=3 + (round(random.random()) * 4)
        )
