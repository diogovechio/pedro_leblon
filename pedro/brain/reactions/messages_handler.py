# Internal
import asyncio

from pedro.brain.modules.agenda import AgendaManager
# External


# Project
from pedro.brain.reactions.default_pedro import pedro_reaction
from pedro.brain.reactions.deprecated_pedro import pedro_deprecado
from pedro.brain.reactions.fact_check import fact_check_reaction
from pedro.brain.reactions.images_reactions import images_reaction
from pedro.brain.reactions.random_reactions import random_reactions
from pedro.brain.reactions.summary_reactions import summary_reaction
from pedro.brain.reactions.agenda_commands import agenda_commands_reaction
from pedro.brain.reactions.complain_swearword import complain_swearword_reaction
from pedro.brain.reactions.emoji_reactions import emoji_reactions
from pedro.brain.reactions.misc_commands import misc_commands_reaction
from pedro.brain.reactions.critic_or_praise import critic_or_praise_reaction
from pedro.brain.reactions.pedro_command import pedro_command_reaction
from pedro.brain.reactions.poll_reaction import poll_reaction
from pedro.brain.reactions.weather_commands import weather_commands_reaction
from pedro.data_structures.daily_flags import DailyFlags
from pedro.data_structures.telegram_message import Message
from pedro.data_structures.bot_config import BotConfig
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.utils.url_utils import check_and_update_with_url_contents


async def messages_handler(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        agenda: AgendaManager,
        llm: LLM,
        allowed_list: list,
        daily_flags: DailyFlags,
        config: BotConfig,
) -> None:
    """
    Handle incoming messages and trigger appropriate reactions.

    Args:
        message (Message): The incoming Telegram message
        history (ChatHistory): Chat history manager instance
        telegram (Telegram): Telegram bot API manager instance
        user_data (UserDataManager): User data management instance
        agenda (AgendaManager): Agenda management instance
        llm (LLM): Language model instance
        allowed_list (list): List of allowed chat IDs
        daily_flags (DailyFlags): Daily feature flags manager
        config (BotConfig): Bot configuration instance

    Returns:
        None
    """
    if message.chat.id in allowed_list:
        updated_message = await check_and_update_with_url_contents(message)

        await asyncio.gather(
            pedro_deprecado(updated_message, history, telegram, user_data, llm, daily_flags),
            images_reaction(updated_message, history, telegram, user_data, llm),
            summary_reaction(updated_message, history, telegram, user_data, llm),
            fact_check_reaction(updated_message, history, telegram, user_data, llm),
            agenda_commands_reaction(updated_message, history, telegram, user_data, agenda, llm),
            complain_swearword_reaction(updated_message, history, telegram, user_data, llm, daily_flags),
            emoji_reactions(updated_message, history, telegram, user_data, llm),
            misc_commands_reaction(updated_message, history, telegram, user_data, llm, daily_flags),
            critic_or_praise_reaction(updated_message, history, telegram, user_data, llm),
            weather_commands_reaction(updated_message, history, telegram, user_data, llm, config),
            random_reactions(updated_message, telegram, user_data, daily_flags),
            pedro_command_reaction(updated_message, history, telegram, llm),
            poll_reaction(updated_message, telegram),
            pedro_reaction(updated_message, history, telegram, user_data, llm, config, daily_flags),
        )
    else:
        await telegram.send_message(
            message_text=str(message.chat.id),
            chat_id=message.chat.id,
        )

        await telegram.leave_chat(message.chat.id)
