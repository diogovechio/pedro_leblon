# Internal
import logging

# Project
from pedro.brain.agent.core import Agent
from pedro.brain.agent.tools.weather import WeatherTool
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.bot_config import BotConfig
from pedro.data_structures.telegram_message import Message
from pedro.utils.text_utils import create_username
from pedro.brain.modules.datetime_manager import DatetimeManager

logger = logging.getLogger(__name__)

async def agent_pedro_reaction(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        llm: LLM,
        config: BotConfig,
) -> None:
    """
    Handle messages starting with "Agente Pedro" using the autonomous Agent.
    """
    if not message.text or not message.text.lower().startswith("agente pedro"):
        return

    # Trigger action typing
    with sending_action(chat_id=message.chat.id, telegram=telegram, user=message.from_.username):
        # 1. Initialize Tools
        weather_tool = WeatherTool(config)
        
        # 2. Initialize Agent
        agent = Agent(llm=llm, tools=[weather_tool])

        # 3. Build System Prompt
        datetime_manager = DatetimeManager()
        user_name = create_username(message.from_.first_name, message.from_.username)
        
        # Get user opinion/sentiment if available
        user_context = ""
        if user_data:
             sentiment = user_data.get_sentiment_level_prompt(message.from_.id)
             user_context = f"\nSobre o usuário {user_name}: {sentiment}"

        system_prompt = (
            "Você é o Pedro, um bot sarcástico, inteligente e útil no Telegram. "
            "Você agora opera como um Agente autônomo capaz de usar ferramentas. "
            "Responda de forma natural e engajante."
            f"Hora atual: {datetime_manager.get_current_time_str()}"
            f"{user_context}"
        )

        # 4. Get History
        # Fetch last 10 messages for context
        chat_logs = history.get_last_messages(chat_id=message.chat.id, limit=10)

        # 5. Run Agent
        # Strip the trigger phrase from the user message
        clean_message = message.text[len("Agente Pedro"):].strip()
        if not clean_message:
            clean_message = "Olá Agente Pedro."

        response = await agent.run(
            user_message=clean_message,
            history=chat_logs,
            system_prompt=system_prompt,
            user_name=user_name
        )

        # 6. Send Response
        await telegram.send_message(
            message_text=response,
            chat_id=message.chat.id,
            reply_to=message.message_id
        )

        # 7. Add to History
        await history.add_message(response, chat_id=message.chat.id, is_pedro=True)
