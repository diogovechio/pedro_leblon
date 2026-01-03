# Internal
import logging
import asyncio
from typing import Optional, Any

# Project
from pedro.brain.agent.core import Agent
from pedro.brain.agent.tools.weather import WeatherTool
from pedro.brain.agent.tools.chat_history_search import ChatHistorySearchTool
from pedro.brain.agent.tools.birthdays import BirthdaySearchTool
from pedro.brain.agent.tools.political_opinions import PoliticalOpinionsTool
from pedro.brain.agent.tools.web_search import WebSearchTool
from pedro.brain.agent.tools.task_list import TaskListTool
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action, FeedbackState
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.task_list import TaskListManager
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.bot_config import BotConfig
from pedro.data_structures.telegram_message import Message
from pedro.utils.text_utils import create_username
from pedro.brain.modules.datetime_manager import DatetimeManager

logger = logging.getLogger(__name__)

async def run_agent_reaction(
    message: Message,
    history: ChatHistory,
    telegram: Telegram,
    user_data: UserDataManager,
    llm: LLM,
    config: BotConfig,
    task_list: TaskListManager,
    image: Any = None,
    send_delay_message: bool = False,
) -> None:
    """
    Common function to initialize and run the Agent with tools.
    
    If send_delay_message is True and processing takes too long, delay messages
    will be sent to the user. When the response is ready, if a delay message was
    sent, it will be edited with the final response instead of sending a new message.
    """
    # Create feedback state to track delay messages
    feedback_state = FeedbackState() if send_delay_message else None
    
    with sending_action(
        chat_id=message.chat.id,
        telegram=telegram,
        user=message.from_.username if send_delay_message else None,
        feedback_state=feedback_state
    ):
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
        clean_message = message.text if message.text else ""
        if image and not clean_message:
            clean_message = "Analise esta imagem."

        response = await agent.run(
            user_message=clean_message,
            history=chat_logs,
            system_prompt=system_prompt,
            user_name=user_name,
            telegram=telegram,
            original_message=message,
            image=image,
        )

        # 6. Send or Edit Response
        # If a delay message was sent, edit it with the final response
        # Otherwise, send a new message
        if feedback_state and feedback_state.last_delay_message_id:
            # Edit the delay message with the final response
            success = await telegram.edit_message(
                message_text=response,
                chat_id=message.chat.id,
                message_id=feedback_state.last_delay_message_id
            )
            if not success:
                # Fallback: send new message if edit fails
                logger.warning("Failed to edit delay message, sending new message instead")
                await telegram.send_message(
                    message_text=response,
                    chat_id=message.chat.id,
                    reply_to=message.message_id
                )
        else:
            # No delay message was sent, send a new message
            await telegram.send_message(
                message_text=response,
                chat_id=message.chat.id,
                reply_to=message.message_id
            )

        # 7. Add to History
        await history.add_message(response, chat_id=message.chat.id, is_pedro=True)

