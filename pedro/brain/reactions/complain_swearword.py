# Internal
import random

# Project
from pedro.brain.constants.constants import SWEAR_WORDS
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.daily_flags import Flags
from pedro.data_structures.telegram_message import Message
from pedro.utils.text_utils import adjust_pedro_casing, get_roletas_from_pavuna


async def complain_swearword_trigger(message: Message) -> bool:
    # 5% chance to trigger the reaction when a swear word is detected
    if not message.text:
        return False

    swear_word_detected = any(
        block_word in message.text.lower() for block_word in SWEAR_WORDS
    )

    return swear_word_detected


async def complain_swearword_reaction(
    message: Message,
    history: ChatHistory,
    telegram: Telegram,
    user_data: UserDataManager,
    llm: LLM,
    daily_flags: Flags
) -> None:
    is_triggered = await complain_swearword_trigger(message)

    if not is_triggered:
        return

    mock_message = ""

    if random.random() < 0.25 and not daily_flags.swearword_complain_today:
        daily_flags.swearword_complain_today = True
        prompts = {
            'critique': 'Critique o linguajar dessa mensagem:',
            'critique_reformule': 'Critique o linguagem dessa mensagem e reformule para uma forma apropriada:',
            'continue': 'Continue a mensagem e critique o linguajar:'
        }

        # Randomly select a prompt from the dictionary
        prompt_key = random.choice(list(prompts.keys()))
        selected_prompt = prompts[prompt_key]

        with sending_action(chat_id=message.chat.id, telegram=telegram):
            prompt = f"{selected_prompt} {message.text}"
            mock_message = await llm.generate_text(
                prompt=prompt,
                model="gpt-3.5-turbo-instruct",
                temperature=1.0,
            )

            mock_message = await adjust_pedro_casing(mock_message)

            await history.add_message(mock_message, chat_id=message.chat.id, is_pedro=True)
            await telegram.send_message(
                message_text=mock_message,
                chat_id=message.chat.id,
                reply_to=message.message_id,
                sleep_time=1 + (round(random.random()) * 4)
            )

    if random.random() < 0.25 and not daily_flags.swearword_random_reaction_today:
        random_messages = await get_roletas_from_pavuna()

        if not random_messages:
            return

        daily_flags.swearword_random_reaction_today = True
        mock_message = random.choice(random_messages)

        await history.add_message(mock_message, chat_id=message.chat.id, is_pedro=True)
        await telegram.send_message(
            message_text=mock_message,
            chat_id=message.chat.id,
            reply_to=None,
            sleep_time=1 + (round(random.random()) * 4)
        )

    if not mock_message:
        return
