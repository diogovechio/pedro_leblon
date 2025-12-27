# Internal
import asyncio
from typing import Any

from pedro.brain.modules.task_list import TaskListManager
# Project
from pedro.brain.reactions.agent_common import run_agent_reaction
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.brain.reactions.fact_check import fact_check
from pedro.data_structures.telegram_message import Message
from pedro.utils.prompt_utils import image_trigger
from pedro.data_structures.bot_config import BotConfig


async def images_reaction(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        llm: LLM,
        config: BotConfig,
        task_list: TaskListManager,
) -> None:
    if message.photo or message.document:
        image = await telegram.image_downloader(message)
        if image and message.from_.username in ["nands93", "decaptor"]:
            with sending_action(chat_id=message.chat.id, telegram=telegram):
                political_prompt = ("Analise esta imagem e verifique se ela contém conteúdo de cunho político ou "
                                    "menciona algum político. "
                                    "Responda apenas com 'SIM', 'PROVÁVEL' ou 'NÃO'. "
                                    "Não elabore ou explique sua resposta.")

                response = await llm.generate_text(political_prompt, model="gpt-4.1-mini", image=image)

                if "SIM" in response.upper() or "PROV" in response.upper():
                    await asyncio.gather(
                        telegram.set_message_reaction(
                            message_id=message.message_id, chat_id=message.chat.id, reaction="💩"
                        ),
                        fact_check(
                            message=message, history=history, telegram=telegram, user_data=user_data, llm=llm
                        )
                    )

        if image and image_trigger(message):
            with sending_action(chat_id=message.chat.id, telegram=telegram, user=message.from_.username):
                await run_agent_reaction(
                    message=message,
                    history=history,
                    telegram=telegram,
                    user_data=user_data,
                    llm=llm,
                    config=config,
                    image=image,
                    task_list=task_list,
                )

    return None
