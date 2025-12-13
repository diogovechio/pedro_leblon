import re

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
) -> None:
    if message.text and message.text.lower().startswith("/pedro"):
        with sending_action(chat_id=message.chat.id, telegram=telegram, user=message.from_.username):
            prompt = await create_vanilla_prompt(
                message=message,
                memory=history,
                telegram=telegram,
                total_messages=4,
                llm=llm
            )

            response = await llm.generate_text(prompt, model="gpt-5-mini")

            response = re.sub(r"^\d{2}:\d{2} - Pedro: ", "", response)

            await history.add_message(response, chat_id=message.chat.id, is_pedro=True)

            await telegram.send_message(
                message_text=response,
                chat_id=message.chat.id,
                reply_to=message.message_id,
            )
