# Internal
import random
import re
import typing as T
from dataclasses import dataclass

# Project
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.telegram_message import Message
from pedro.utils.prompt_utils import get_photo_description
from pedro.utils.text_utils import adjust_pedro_casing


async def tldr_trigger(message: Message) -> bool:
    return message.text and message.text.lower().startswith("/tldr")


async def tlsr_trigger(message: Message) -> bool:
    return message.text and message.text.lower().startswith("/tlsr")


async def tlfr_trigger(message: Message) -> bool:
    return message.text and message.text.lower().startswith("/tlfr")


async def handle_reply_to_message(
    message: Message,
    history: ChatHistory,
    telegram: Telegram,
    llm: LLM,
    topics: bool,
    tlfr: bool,
) -> str:
    prompt = "faça um resumo do texto a seguir:"
    if topics:
        prompt = "em no máximo 7 tópicos de no máximo 6 palavras cada, " + prompt
    elif tlfr:
        prompt = "de maneira distorcida e levemente sensacionalista, " + prompt

    if message.reply_to_message.photo:
        image_description = await get_photo_description(
            telegram=telegram,
            llm=llm,
            message=message.reply_to_message,
            extra_prompt=message.text,
        )
        input_text = f"[[IMAGE]]: {image_description}"
    else:
        input_text = message.reply_to_message.text or ""

    summary = await llm.generate_text(
        prompt=f"{prompt} {input_text}",
    )

    summary = await adjust_pedro_casing(summary.lower())

    await history.add_message(summary, chat_id=message.chat.id, is_pedro=True)

    await telegram.send_message(
        message_text=summary,
        chat_id=message.chat.id,
        reply_to=message.message_id
    )

    return summary


async def handle_command_with_parameters(
    message: Message,
    history: ChatHistory,
    telegram: Telegram,
    user_data: UserDataManager,
    llm: LLM,
    topics: bool,
    tlfr: bool,
    days: int
) -> str:
    first_text = message.text.split(" ")[0]
    days_match = re.search(r"\d+", first_text)
    days = int(days_match.group(0)) if days_match else days

    search_text = message.text.replace(first_text, "").strip().lower()
    search_text = search_text.replace(str(days), "").strip()

    if search_text.startswith("@"):
        search_text = search_text.replace("@", "")

    chat_history = history.get_friendly_last_messages(
        chat_id=message.chat.id,
        days=days,
        limit=150
    )

    prompt = ""
    if search_text:
        for user in user_data.get_users():
            if search_text.lower() in user.lower():
                prompt = f'resuma o que {user} tem falado na conversa abaixo'
                break

        if not prompt:
            prompt = f'resuma o que foi falado sobre o tema "{search_text}" na conversa abaixo'
    else:
        if not days or days < 2:
            prompt = "em no máximo 500 caracteres, faça um resumo da conversa abaixo"
        else:
            prompt = "detalhando tudo o que foi conversado, faça um resumo da conversa abaixo"

    if topics:
        prompt = "em no máximo 7 tópicos de no máximo 6 palavras cada, " + prompt
    elif tlfr:
        prompt = "de maneira distorcida e levemente sensacionalista, " + prompt

    summary = await llm.generate_text(
        prompt=f"{prompt}:\n\n{chat_history}",
        model="gpt-5-nano",
        temperature=1.0
    )

    summary = await adjust_pedro_casing(summary.lower())

    await history.add_message(summary, chat_id=message.chat.id, is_pedro=True)

    await telegram.send_message(
        message_text=summary,
        chat_id=message.chat.id,
        reply_to=message.message_id
    )

    return summary


async def handle_basic_summarization(
    message: Message,
    history: ChatHistory,
    telegram: Telegram,
    llm: LLM,
    topics: bool,
    tlfr: bool,
) -> str:
    chat_history = history.get_friendly_messages_since_last_from_user(
        chat_id=message.chat.id,
        user_id=message.from_.id
    )

    if topics:
        prompt = "em no máximo 7 tópicos de no máximo 6 palavras cada, " \
                 "cite de maneira enumerada os principais temas discutidos na conversa abaixo"
    elif tlfr:
        prompt = random.choice([
            "de maneira distorcida e levemente sensacionalista, faça um pequeno resumo da conversa abaixo",
            f"de maneira distorcida e levement sensacionalista, faça um pequeno resumo da conversa de {message.from_.first_name} e seus amigos"],
        )
    else:
        prompt = random.choice(
            ["em no máximo 500 caracteres, faça um resumo da conversa abaixo",
             f"em no máximo 500 caracteres, faça um curto resumo da conversa de {message.from_.first_name} e seus amigos"],
        )

    summary = await llm.generate_text(
        prompt=f"{prompt}:\n\n{chat_history}",
        temperature=1.0
    )

    summary = await adjust_pedro_casing(summary.lower())

    await history.add_message(summary, chat_id=message.chat.id, is_pedro=True)

    await telegram.send_message(
        message_text=summary,
        chat_id=message.chat.id,
        reply_to=message.message_id,
    )

    return summary


async def update_chat_title(
    message: Message,
    telegram: Telegram,
    llm: LLM,
    summary: str
) -> None:
    if message.chat.id != -1001369599178:
        return

    title_prompt = "com base no texto abaixo, sugira o nome de um chat em no máximo 4 palavras:\n\n"
    title_prompt += summary

    new_chat_title = await llm.generate_text(
        prompt=title_prompt,
        temperature=1.0
    )

    if '"' in new_chat_title:
        idx = new_chat_title.find('"')
        new_chat_title = new_chat_title[idx + 1:]
        new_chat_title = new_chat_title.replace('"', "")

    if " " in new_chat_title:
        first_word = new_chat_title.split(" ")[0]
        new_chat_title = new_chat_title.replace(first_word, "BLA")
    else:
        new_chat_title = "BLA " + new_chat_title

    if "asd" in message.chat.title.lower():
        new_chat_title = new_chat_title.replace("BLA", "ASD")

    chat_title = ""
    for char in new_chat_title:
        if "1" in new_chat_title:
            new_chat_title = new_chat_title.replace("1", "")
        if char.isdigit():
            break
        chat_title += char

    await telegram.set_chat_title(
        chat_id=message.chat.id,
        title=chat_title
    )


async def summary_reaction(
    message: Message,
    history: ChatHistory,
    telegram: Telegram,
    user_data: UserDataManager,
    llm: LLM,
) -> None:
    is_tldr = await tldr_trigger(message)
    is_tlsr = await tlsr_trigger(message)
    is_tlfr = await tlfr_trigger(message)

    if not (is_tldr or is_tlsr or is_tlfr):
        return

    topics = is_tlsr
    tlfr = is_tlfr
    days = 5

    with sending_action(chat_id=message.chat.id, telegram=telegram, user=message.from_.username):
        if message.reply_to_message:
            summary = await handle_reply_to_message(message, history, telegram, llm, topics, tlfr)
        elif " " in message.text or any(letter.isdigit() for letter in message.text):
            summary = await handle_command_with_parameters(message, history, telegram, user_data, llm, topics, tlfr, days)
        else:
            summary = await handle_basic_summarization(message, history, telegram, llm, topics, tlfr)

        await update_chat_title(message, telegram, llm, summary)
