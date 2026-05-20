import re
import asyncio

# Internal
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.data_structures.telegram_message import Message
from pedro.utils.prompt_utils import create_vanilla_prompt


async def pedro_command_reaction(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        llm: LLM,
        memory_manager = None,
) -> None:
    if message.text and message.text.lower().startswith("/pedro"):
        with sending_action(chat_id=message.chat.id, telegram=telegram, user=message.from_.username):
            prompt = await create_vanilla_prompt(
                message=message,
                chat_history=history,
                telegram=telegram,
                total_messages=4,
                llm=llm
            )

            memory_context = ""
            if memory_manager:
                chat_memory = memory_manager.get_memory_by_chat_id(message.chat.id)
                if chat_memory:
                    memory_context = f"Memória de conversas anteriores:\n{chat_memory}\n\n"

            prompt = memory_context + prompt

            response = await llm.generate_text(prompt, model="gpt-5-mini")

            response = re.sub(r"^\d{2}:\d{2} - Pedro: ", "", response)

            await history.add_message(response, chat_id=message.chat.id, is_pedro=True)

            await telegram.send_message(
                message_text=response,
                chat_id=message.chat.id,
                reply_to=message.message_id,
            )

            # Update memory in the background
            if memory_manager:
                chat_history_text = history.get_friendly_last_messages(chat_id=message.chat.id, limit=10)
                asyncio.create_task(
                    memory_manager.upsert_memory_by_chat_id(message.chat.id, chat_history_text)
                )

