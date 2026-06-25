# Internal
import logging
import asyncio
import html
import random
from typing import Optional

# Project
from pedro.brain.agent.core import Agent
from pedro.brain.agent.tools.web_search import WebSearchTool
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.telegram_message import Message
from pedro.utils.prompt_utils import get_photo_description, send_telegram_log
from pedro.utils.text_utils import adjust_pedro_casing, create_username

logger = logging.getLogger(__name__)


async def fact_check_2_reaction(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        llm: LLM,
) -> None:
    if message.text and message.text.lower().startswith(("/factcheck2", "/factcheck 2")):
        await fact_check_2(message, history, telegram, user_data, llm)


async def fact_check_2(
    message: Message,
    history: ChatHistory,
    telegram: Telegram,
    user_data: UserDataManager,
    llm: LLM,
) -> None:
    mentiroso_argument = ""
    mentiroso = ""
    reply_to = message.message_id

    # 1. Check if we have a target message (reply_to_message) or photo
    if message.reply_to_message:
        reply_to = message.reply_to_message.message_id
        if message.reply_to_message.text:
            mentiroso_argument = message.reply_to_message.text
            mentiroso = message.reply_to_message.from_.first_name
        elif message.reply_to_message.photo:
            mentiroso_argument = await get_photo_description(telegram, llm, message.reply_to_message)
            mentiroso = message.reply_to_message.from_.first_name
    elif message.photo:
        mentiroso_argument = await get_photo_description(telegram, llm, message)
        mentiroso = message.from_.first_name

    # 2. Get history (up to last 7 messages, excluding the current factcheck2 command)
    chat_logs = history.get_last_messages(chat_id=message.chat.id, limit=8)
    
    # Exclude command message
    filtered_logs = []
    for log in chat_logs:
        if log.message.strip().lower().startswith(("/factcheck2", "/factcheck 2")):
            continue
        filtered_logs.append(log)
    
    filtered_logs = filtered_logs[-7:]

    # 3. Process fact check using ReAct Agent
    with sending_action(chat_id=message.chat.id, telegram=telegram):
        # Initialize WebSearchTool and Agent
        web_search_tool = WebSearchTool()
        agent = Agent(llm=llm, tools=[web_search_tool])
        
        # System prompt for fact-checking agent
        # MUST suggest using the tool 'web_search' to get precise information.
        # MUST maintain a progressive/materialist view.
        # MUST follow Pedro's lowercase, no period, informal persona.
        system_prompt = (
            "Você é o Pedro, um especialista em verificação de fatos (fact-checking) no Telegram. "
            "Sua missão é analisar de forma crítica as afirmações de fato feitas na conversa ou na mensagem respondida, "
            "trazendo informações precisas e verificadas da internet. "
            "Você DEVE usar a ferramenta 'web_search' para pesquisar na internet até obter informações precisas "
            "e atualizadas sobre o assunto verificado. Não dê respostas baseadas apenas no seu conhecimento prévio "
            "se o tema envolver fatos atuais ou dados específicos. "
            "Mantenha sempre uma tendência a visões progressistas, materialistas e de defesa dos direitos sociais e da "
            "classe trabalhadora ao avaliar os temas, combatendo desinformações, fake news, preconceitos, discursos de ódio "
            "ou visões elitistas e reacionárias. "
            "Responda de forma sarcástica, inteligente e informal. Organize cada parágrafo com duas quebras de linha."
            "Seja sucinto, não se estenda mais que o necessário, mas não omita informações cruciais. "
            "Não mande links. Não faça perguntas."
        )

        # Prepare user_message for agent
        user_name = create_username(message.from_.first_name, message.from_.username)
        if mentiroso_argument:
            user_message = f"verifique o argumento de {mentiroso}: '{mentiroso_argument}'"
        else:
            user_message = "verifique as afirmações de fato feitas na conversa recente acima"

        # Send log to telegram log chat in the background
        log_message = (
            f"<b>[Fact Check 2 Agent Reaction Log]</b>\n"
            f"<b>Chat ID:</b> {message.chat.id}\n"
            f"<b>User Message:</b> {html.escape(user_message)}\n\n"
            f"<b>System Prompt:</b>\n{html.escape(system_prompt)}"
        )
        asyncio.create_task(
            send_telegram_log(
                telegram=telegram,
                message_text=log_message,
                parse_mode="HTML"
            )
        )

        try:
            # Run agent
            response = await agent.run(
                user_message=user_message,
                history=filtered_logs,
                system_prompt=system_prompt,
                user_name=user_name,
                telegram=telegram,
                original_message=message,
            )

            # Format output using adjust_pedro_casing to ensure persona guidelines (no final period, lowercase first char, etc.)
            formatted_response = await adjust_pedro_casing(response)

            # Split response into parts by double newline "\n\n"
            parts = [p.strip() for p in formatted_response.split("\n\n") if p.strip()]

            for i, part in enumerate(parts):
                await asyncio.gather(
                    history.add_message(part, chat_id=message.chat.id, is_pedro=True),
                    telegram.send_message(
                        message_text=part,
                        chat_id=message.chat.id,
                        reply_to=reply_to if i == 0 else None,
                        sleep_time=3.0 + random.random() * 6.0 if i != 0 else 0,
                        disable_web_page_preview=True
                    )
                )

        except Exception as e:
            logger.exception(f"Error executing factcheck2 reaction: {e}")
            error_msg = "deu ruim na hora de pesquisar as paradas"
            await telegram.send_message(
                message_text=error_msg,
                chat_id=message.chat.id,
                reply_to=reply_to
            )
            await history.add_message(error_msg, chat_id=message.chat.id, is_pedro=True)
