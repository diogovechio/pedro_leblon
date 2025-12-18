# Project
import random
import asyncio

from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.daily_flags import DailyFlags
from pedro.data_structures.telegram_message import Message
from pedro.utils.prompt_utils import create_basic_prompt, text_trigger, random_trigger, check_web_search, send_telegram_log, \
    create_self_complement_prompt, negative_response
from pedro.utils.text_utils import adjust_pedro_casing
from pedro.utils.url_utils import https_url_extract


async def default(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        llm: LLM,
        daily_flags: DailyFlags,
) -> None:
    _text_trigger = text_trigger(message)
    _random_trigger = random_trigger(message=message, daily_flags=daily_flags)

    if _text_trigger or _random_trigger:
        await user_data.adjust_sentiment(message)

        with sending_action(chat_id=message.chat.id, telegram=telegram, user=message.from_.username if _text_trigger else None):
            web_search = check_web_search(message)
            model = "gpt-4.1-mini" if web_search else "gpt-4.1-nano"

            prompt = await create_basic_prompt(
                message, history,
                user_data=user_data,
                total_messages=3 if web_search else 7,
                telegram=telegram,
                llm=llm
            )

            response = await adjust_pedro_casing(
                await llm.generate_text(prompt, model=model, web_search=web_search)
            )

            if negative_response(response) and not web_search and len(response) < 100:
                prompt = await create_basic_prompt(
                    message, history,
                    user_data=user_data,
                    total_messages=2,
                    telegram=telegram,
                    llm=llm
                )

                model = "gpt-4.1-mini"
                response = await adjust_pedro_casing(
                    await llm.generate_text(prompt, model=model, web_search=web_search)
                )

            await history.add_message(response, chat_id=message.chat.id, is_pedro=True)

            await telegram.send_message(
                message_text=response,
                chat_id=message.chat.id,
                reply_to=message.message_id,
                disable_web_page_preview=web_search
            )

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
