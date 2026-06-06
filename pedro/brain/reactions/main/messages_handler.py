# Internal
import asyncio
import math
import time

from pedro.brain.modules.agenda import AgendaManager
from pedro.brain.modules.task_list import TaskListManager
# External


# Project
from pedro.brain.reactions.main.default_pedro import pedro_reaction
from pedro.brain.reactions.fact_check import fact_check_reaction
from pedro.brain.reactions.main.images_reactions import images_reaction
from pedro.brain.reactions.random_reactions import random_reactions
from pedro.brain.reactions.summary_reactions import summary_reaction
from pedro.brain.reactions.agenda_commands import agenda_commands_reaction
from pedro.brain.reactions.task_commands import task_commands_reaction
from pedro.brain.reactions.complain_swearword import complain_swearword_reaction
from pedro.brain.reactions.emoji_reactions import emoji_reactions
from pedro.brain.reactions.misc_commands import misc_commands_reaction
from pedro.brain.reactions.critic_or_praise import critic_or_praise_reaction
from pedro.brain.reactions.pedro_command import pedro_command_reaction
from pedro.brain.reactions.poll_reaction import poll_reaction
from pedro.brain.reactions.weather_commands import weather_commands_reaction
from pedro.data_structures.daily_flags import Flags
from pedro.data_structures.telegram_message import Message
from pedro.data_structures.bot_config import BotConfig
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.utils.url_utils import check_and_update_with_url_contents
from pedro.utils.prompt_utils import text_trigger, image_trigger


async def messages_handler(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        agenda: AgendaManager,
        task_list: TaskListManager,
        llm: LLM,
        allowed_list: list,
        flags: Flags,
        config: BotConfig,
        memory_manager = None,
) -> None:
    """
    Handle incoming messages and trigger appropriate reactions.

    Args:
        message (Message): The incoming Telegram message
        history (ChatHistory): Chat history manager instance
        telegram (Telegram): Telegram bot API manager instance
        user_data (UserDataManager): User data management instance
        agenda (AgendaManager): Agenda management instance
        task_list (TaskListManager): Task list management instance
        llm (LLM): Language model instance
        allowed_list (list): List of allowed chat IDs
        flags (Flags): Daily feature flags manager
        config (BotConfig): Bot configuration instance
        memory_manager (MemoryManager, optional): Memory manager instance

    Returns:
        None
    """
    if message.chat.id in allowed_list:
        updated_message = await check_and_update_with_url_contents(message)

        # Rate limit check for users without a username
        if updated_message.from_ and not updated_message.from_.username:
            is_triggered = (
                (updated_message.text and updated_message.text.startswith("/")) or
                text_trigger(updated_message) or
                ((updated_message.photo or updated_message.document) and image_trigger(updated_message))
            )

            if is_triggered:
                db = user_data.database
                user_id = updated_message.from_.id
                current_time = time.time()
                one_hour_ago = current_time - 600

                # Fetch records from database
                records = db.search("rate_limits", {"user_id": user_id})

                active_records = []
                for record in records:
                    ts = record.get("timestamp")
                    if ts is not None:
                        if ts < one_hour_ago:
                            # Clean up expired triggers
                            db.remove("rate_limits", {"user_id": user_id, "timestamp": ts})
                        else:
                            active_records.append(record)

                if len(active_records) >= 7:
                    active_records.sort(key=lambda x: x["timestamp"])
                    t_old = active_records[0]["timestamp"]
                    remaining_seconds = t_old + 600 - current_time
                    remaining_minutes = max(1, math.ceil(remaining_seconds / 60))

                    response_text = f"já deu de conversar agora, voltamos a falar em {remaining_minutes} minutos"
                    await history.add_message(response_text, chat_id=updated_message.chat.id, is_pedro=True)
                    await telegram.send_message(
                        message_text=response_text,
                        chat_id=updated_message.chat.id,
                        reply_to=updated_message.message_id,
                    )
                    return

                # Record the new trigger timestamp
                db.insert("rate_limits", {"user_id": user_id, "timestamp": current_time})

        await asyncio.gather(
            images_reaction(updated_message, history, telegram, user_data, llm, config, task_list, memory_manager),
            summary_reaction(updated_message, history, telegram, user_data, llm),
            fact_check_reaction(updated_message, history, telegram, user_data, llm),
            agenda_commands_reaction(updated_message, history, telegram, user_data, agenda, llm),
            task_commands_reaction(updated_message, history, telegram, user_data, task_list, llm),
            complain_swearword_reaction(updated_message, history, telegram, user_data, llm, flags),
            emoji_reactions(updated_message, history, telegram, user_data, llm),
            misc_commands_reaction(updated_message, history, telegram, user_data, llm, flags),
            critic_or_praise_reaction(updated_message, history, telegram, user_data, llm),
            weather_commands_reaction(updated_message, history, telegram, user_data, llm, config),
            random_reactions(updated_message, telegram, user_data, flags),
            pedro_command_reaction(updated_message, history, telegram, llm, memory_manager),
            poll_reaction(updated_message, telegram),
            pedro_reaction(updated_message, history, telegram, user_data, llm, config, flags, task_list, memory_manager),
        )
    else:
        await telegram.send_message(
            message_text=str(message.chat.id),
            chat_id=message.chat.id,
        )

        await telegram.leave_chat(message.chat.id)

