import random
import asyncio

from pedro.brain.constants.constants import POLITICAL_OPINIONS, POLITICAL_WORDS
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.datetime_manager import DatetimeManager
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.daily_flags import DailyFlags
from pedro.data_structures.telegram_message import Message, ReplyToMessage
from pedro.utils.text_utils import create_username
import logging

logger = logging.getLogger(__name__)


async def send_telegram_log(
        telegram: Telegram,
        message_text: str,
        parse_mode: str = "HTML",
        message=None
) -> None:
    log_chat_id = -1002051541243
    if message:
        try:
            chat_name = message.chat.title if hasattr(message.chat, 'title') and message.chat.title else str(message.chat.id)
            user_name = create_username(message.from_.first_name, message.from_.username) if message.from_ else "Unknown"
            log_message = f"Prompt gerado para chat: {chat_name}\nUsuário: {user_name}"
            await telegram.send_message(message_text=log_message, chat_id=log_chat_id, parse_mode="HTML")
            logger.info(f"Prompt sent to log chat {log_chat_id}")
        except Exception as e:
            logger.error(f"Failed to send prompt to log chat: {e}")

    # Maximum message length
    max_message_length = 1500

    # If message is shorter than the maximum length, send it directly
    if len(message_text) <= max_message_length:
        await telegram.send_message(
            message_text=message_text,
            chat_id=log_chat_id,
            parse_mode=parse_mode,
        )
        return

    # Split message into chunks of maximum length
    chunks = []
    for i in range(0, len(message_text), max_message_length):
        chunks.append(message_text[i:i + max_message_length])

    # Send each chunk sequentially
    for i, chunk in enumerate(chunks):
        # Add a prefix to indicate this is part of a multi-part message
        prefix = f"[Parte {i+1}/{len(chunks)}]\n" if len(chunks) > 1 else ""

        await telegram.send_message(
            message_text=prefix + chunk,
            chat_id=log_chat_id,
            parse_mode=parse_mode,
        )


async def process_reply_message(llm: LLM, telegram: Telegram, message: Message) -> str:
    if not message.reply_to_message:
        return ""

    reply = message.reply_to_message
    sender_name = create_username(reply.from_.first_name, reply.from_.username) if reply.from_ else "Unknown"
    sender_name = f"{reply.from_.first_name} - {sender_name}"

    if reply.photo:
        image_description = await get_photo_description(llm=llm, telegram=telegram, message=reply, extra_prompt=message.text)
        return f" ->> [... {sender_name} havia enviado a imagem: {image_description} ]"
    elif reply.document and reply.document.mime_type == "application/pdf":
        doc_description = await get_doc_description(llm=llm, telegram=telegram, message=reply, extra_prompt=message.text)
        return f" ->> [... {sender_name} havia enviado um documento PDF: {doc_description} ]"
    else:
        reply_text = reply.text or ""
        return f" ->>  [... {sender_name} havia dito anteriormente: [[{reply_text}]] ]"


async def create_basic_prompt(
        message: Message,
        memory: ChatHistory,
        user_data: UserDataManager | None,
        total_messages=15,
        telegram: Telegram | None = None,
        llm: LLM | None = None,
) -> str:
    base_prompt = ""

    datetime = DatetimeManager()

    chat_history = memory.get_friendly_last_messages(chat_id=message.chat.id, limit=total_messages)
    users_opinions = []

    political_opinions = ""
    if any(political_word.lower() in chat_history.lower() for political_word in POLITICAL_WORDS):
        political_opinions = "\n".join(POLITICAL_OPINIONS)
        political_opinions = f"{political_opinions}\n\n"

    text = message.caption if message.caption else message.text

    reply_text = ""
    if message.reply_to_message:
        reply_text = await process_reply_message(message=message, telegram=telegram, llm=llm)

    user_message = f"{text} {reply_text}"

    if message.text:
        base_prompt += (f"Você é o Pedro, responda a mensagem enviada por "
                       f"{create_username(message.from_.first_name, message.from_.username)} "
                       f"na conversa: ## {user_message} ##.\n\n")
    elif message.photo:
        base_prompt += (f"Você é o Pedro, responda sobre imagem enviada por"
                       f" {create_username(message.from_.first_name, message.from_.username)} "
                       f"na conversa: ## {user_message} ##.\n\n")

    if user_data:
        users_opinions = user_data.get_users_by_text_match(chat_history)

        base_prompt += f"{user_data.get_sentiment_level_prompt(message.from_.id)}\n\n"

    opinions_text = ""

    for user_opinion in users_opinions:
        if user_opinion.opinions:
            if user_opinion.username and "pedroleblonbot" in user_opinion.username:
                continue

            user_display_name = create_username(user_opinion.first_name, user_opinion.username)
            user_display_name = f"{user_opinion.first_name} - {user_display_name}"
            user_opinions_text = "\n".join([f"Sobre {user_display_name}: {opinion[:100]}" for opinion in user_opinion.opinions])
            opinions_text += f"### RESPONDA COM BASE NAS INFORMAÇÕES A SEGUIR SE FOR PERGUNTADO SOBRE ***{user_display_name}*** ### \n{user_opinions_text}\n\n"

    prompt = base_prompt + political_opinions + opinions_text + chat_history + reply_text + f"\n{datetime.get_current_time_str()} - Pedro (pedroleblonbot): "

    if telegram:
        asyncio.create_task(send_telegram_log(
            telegram=telegram,
            message_text=prompt,
            message=message
        ))

    return prompt


async def create_self_complement_prompt(
        history: ChatHistory,
        chat_id: int,
        telegram: Telegram,
        llm: LLM,
        user_data: UserDataManager = None,
        total_messages=5
) -> str:
    datetime = DatetimeManager()

    chat_history = history.get_friendly_last_messages(chat_id=chat_id, limit=total_messages)

    if random.random() < 0.7:
        base_prompt = (
            "Você é o Pedro. Complemente a mensagem que acabou de enviar. Seja sucinto, em no máximo 7 palavras. "
            "Não faça novos cumprimentos. "
            "Não repita o que já foi dito, apenas complemente.\n\n"
        )
    else:
        base_prompt = (
            "Você é o Pedro. Complemente a mensagem que acabou de enviar. Porém dessa vez seja passivo agressivo. "
            "Seja sucinto, em no máximo 5 palavras. Sua mensagem deve complementar a sua anterior.\n\n"
        )

    prompt = base_prompt + chat_history + f"\n{datetime.get_current_time_str()} - Pedro (pedroleblonbot):"

    if telegram:
        asyncio.create_task(
            send_telegram_log(
                telegram=telegram,
                message_text=prompt
            )
        )

    return prompt


def text_trigger(message: Message, daily_flags: DailyFlags) -> bool:
    if message.text and message.text.startswith("/pedro"):
        return False

    if random.random() < 0.15 and not daily_flags.random_talk_today and not message.text.startswith("/"):
        daily_flags.random_talk_today = True

        return True

    return (
            message.text and
            (message.text.lower().startswith("pedro") or message.text.lower().replace("?", "").strip().endswith(
                "pedro") or message.chat.id > 0)
    ) or (
            message.reply_to_message and "pedro" in message.reply_to_message.from_.username and not message.text.startswith("/")
    )

def image_trigger(message: Message) -> bool:
    return (
            message.caption and
            (message.caption.lower().startswith("pedro") or message.caption.lower().replace("?", "").strip().endswith(
                "pedro") or message.chat.id > 0)
    )


def negative_response(text: str) -> bool:
    return any(word in text.lower() for word in ["desculpe,", "desculpa,", "desculpas,", "não posso ", "não vou "])


async def get_photo_description(
        telegram: Telegram,
        llm: LLM,
        message: ReplyToMessage | Message,
        extra_prompt: None | str = None,
) -> str:
    if not telegram or not llm:
        logger.warning("Telegram or LLM not provided, cannot process reply photo")
        return ""

    if not message.photo:
        return ""

    try:
        temp_message = Message(
            from_=message.from_,
            message_id=message.message_id,
            chat=message.chat,
            date=message.date,
            text=message.text,
            photo=message.photo,
            caption=message.caption
        )

        image = await telegram.image_downloader(temp_message)
        if not image:
            logger.warning("Failed to download reply photo")
            return ""

        prompt = "Descreva a imagem com o máximo de detalhes identificáveis"
        if extra_prompt:
            prompt = "Sobre a imagem: " + extra_prompt
        caption = f'Legenda: {temp_message.caption}: ' if temp_message.caption else ""
        description = await llm.generate_text(prompt=prompt, image=image, model="gpt-4.1-mini")

        return f"[[{caption}IMAGEM ANEXADA: {description} ]]"
    except Exception as e:
        logger.exception(f"Error processing reply photo: {e}")
        return ""


async def get_doc_description(
        telegram: Telegram,
        llm: LLM,
        message: ReplyToMessage | Message,
        extra_prompt: None | str = None,
) -> str:
    if not telegram or not llm:
        logger.warning("Telegram or LLM not provided, cannot process reply document")
        return ""

    if not message.document or message.document.mime_type != "application/pdf":
        return ""

    try:
        temp_message = Message(
            from_=message.from_,
            message_id=message.message_id,
            chat=message.chat,
            date=message.date,
            text=message.text,
            document=message.document,
            caption=message.caption
        )

        document = await telegram.document_downloader(temp_message)
        if not document:
            logger.warning("Failed to download reply document")
            return ""

        prompt = f"Descreva o conteúdo deste documento PDF chamado '{document.file_name}' com o máximo de detalhes identificáveis"
        if extra_prompt:
            prompt = f"Sobre o documento PDF '{document.file_name}': " + extra_prompt

        caption = f'Legenda: {temp_message.caption}: ' if temp_message.caption else ""
        description = await llm.generate_text(prompt=prompt, model="gpt-4.1-mini", document=document)

        return f"[[{caption}DOCUMENTO PDF ANEXADO: {description} ]]"
    except Exception as e:
        logger.exception(f"Error processing reply document: {e}")
        return ""


def check_web_search(message: Message) -> bool:
    return any(word in message.text.lower() for word in ["tempo", "previs", "clima", "cotação", "fonte", "pesquis", "google", "internet", "verifique", "busque", "notícia", "noticia"])


async def create_vanilla_prompt(
        message: Message,
        memory: ChatHistory,
        total_messages=15,
        telegram: Telegram | None = None,
        llm: LLM | None = None,
) -> str:
    datetime = DatetimeManager()

    chat_history = memory.get_friendly_last_messages(chat_id=message.chat.id, limit=total_messages)

    text = message.caption if message.caption else message.text
    text = text.replace("/pedro", "").strip()

    reply_text = ""
    if message.reply_to_message:
        reply_text = await process_reply_message(message=message, telegram=telegram, llm=llm)

    user_message = f"{text} {reply_text}"

    prompt = (f"### Complete o chat com uma resposta de Pedro ao final da conversa. Restrição: "
              f"Não repita seu nome na mensagem que for gerada ####"
              f"\n\n{chat_history}\n{create_username(message.from_.first_name, message.from_.username)}:"
              f" {user_message}\n{datetime.get_current_time_str()} - Pedro:")

    if telegram:
        asyncio.create_task(send_telegram_log(
            telegram=telegram,
            message_text=prompt,
            message=message
        ))

    return prompt
