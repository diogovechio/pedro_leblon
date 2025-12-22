# Internal
import logging
import random
import asyncio

# Project
from pedro.brain.agent.core import Agent
from pedro.brain.agent.tools.weather import WeatherTool
from pedro.brain.agent.tools.chat_history_search import ChatHistorySearchTool
from pedro.brain.agent.tools.birthdays import BirthdaySearchTool
from pedro.brain.agent.tools.political_opinions import PoliticalOpinionsTool
from pedro.brain.agent.tools.web_search import WebSearchTool
from pedro.brain.agent.tools.task_list import TaskListTool
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.bot_config import BotConfig
from pedro.data_structures.daily_flags import Flags
from pedro.data_structures.telegram_message import Message
from pedro.utils.text_utils import create_username, adjust_pedro_casing
from pedro.utils.prompt_utils import text_trigger, random_trigger, create_self_complement_prompt, check_web_search
from pedro.brain.modules.datetime_manager import DatetimeManager

logger = logging.getLogger(__name__)

async def pedro_reaction(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        llm: LLM,
        config: BotConfig,
        daily_flags: Flags,
        task_list,
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
        # 1. Initialize Tools
        weather_tool = WeatherTool(config)
        chat_history_tool = ChatHistorySearchTool(history, message.chat.id)
        birthday_tool = BirthdaySearchTool(message.chat.id)
        politics_tool = PoliticalOpinionsTool()
        web_search_tool = WebSearchTool()
        task_list_tool = TaskListTool(message.from_.id, message.chat.id, task_list)

        # 2. Initialize Agent
        agent = Agent(llm=llm, tools=[weather_tool, chat_history_tool, birthday_tool, politics_tool, web_search_tool, task_list_tool])

        # 3. Build System Prompt
        datetime_manager = DatetimeManager()
        user_name = create_username(message.from_.first_name, message.from_.username)
        
        # Get user opinion/sentiment if available
        user_context = ""
        opinions_text = ""

        # Get opinions about other users mentioned in the conversation
        if user_data:
            sentiment = user_data.get_sentiment_level_prompt(message.from_.id)
            user_context = f"\nSobre o usuário {user_name}: {sentiment}"
            # Get chat history to find mentioned users
            chat_history_text = history.get_friendly_last_messages(chat_id=message.chat.id, limit=10)
            users_opinions = user_data.get_users_by_text_match(chat_history_text)
            
            for user_opinion in users_opinions:
                if user_opinion.opinions:
                    # Skip Pedro himself
                    if user_opinion.username and "pedroleblonbot" in user_opinion.username:
                        continue
                    
                    user_display_name = create_username(user_opinion.first_name, user_opinion.username)
                    user_display_name = f"{user_opinion.first_name} - {user_display_name}"
                    user_opinions_text = "\n".join([f"Sobre {user_display_name}: {opinion[:100]}" for opinion in user_opinion.opinions])
                    opinions_text += f"### RESPONDA COM BASE NAS INFORMAÇÕES A SEGUIR SE FOR PERGUNTADO SOBRE ***{user_display_name}*** ### \n{user_opinions_text}\n\n"

        system_prompt = (
            "Você é o Pedro, um usuário sarcástico, inteligente e útil no Telegram. "
            "Você é capaz de usar ferramentas para trazer diversas informações. "
            "Responda de forma natural, no mesmo estilo de mensagem de outros participantes na conversa, "
            "Escreva com iniciais minúsculas e sem ponto final caso você esteja gerando uma resposta informal. "
            "Evite excesso de cumprimentos e formalidades. "
            "Evite excesso de pontuação. "
            "Evite excesso de empolgação. "
            "Evite perguntas desnecessárias. "
            "Você conversa num estilo informal de usuário de internet.\n\n"
            f"Hora atual: {datetime_manager.get_current_time_str()}\n"
            f"Data atual: {datetime_manager.get_current_date_str()}\n"
            f"{user_context}\n"
            f"{opinions_text}"
        )

        # 4. Get History
        # Fetch last 10 messages for context
        chat_logs = history.get_last_messages(chat_id=message.chat.id, limit=10)

        # 5. Run Agent
        # Use the full message text, letting the agent understand the context
        clean_message = message.text

        response = await agent.run(
            user_message=clean_message,
            history=chat_logs,
            system_prompt=system_prompt,
            user_name=user_name,
            telegram=telegram,
            original_message=message
        )

        # 6. Send Response
        await telegram.send_message(
            message_text=response,
            chat_id=message.chat.id,
            reply_to=message.message_id
        )

        # 7. Add to History
        await history.add_message(response, chat_id=message.chat.id, is_pedro=True)

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
