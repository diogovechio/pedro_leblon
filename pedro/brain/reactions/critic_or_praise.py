# Internal
import random
import re

# Project
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.telegram_message import Message, From, Chat, ReplyToMessage
from pedro.utils.prompt_utils import get_photo_description

# Constants
OPENAI_TRASH_LIST = ["pedro:", "pedro", "pedro leblon:", "pedro leblon"]

async def critic_or_praise_reaction(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        llm: LLM,
) -> None:
    if message.text and (
            message.text.startswith("/critique") or
            message.text.startswith("/elogie") or
            message.text.startswith("/simpatize") or
            message.text.startswith("/humilhe")
    ):
        await _critic_or_praise(message, telegram, llm, history, user_data)
        return

    # Check for watched words from the message sender
    if message.text:
        user = user_data.get_user_data(message.from_.id)
        if user and user.watched_words:
            normalized_message = re.sub(r'([a-zà-úç])\1+', r'\1', message.text.lower()).replace(" ", "")
            for word in user.watched_words:
                normalized_word = re.sub(r'([a-zà-úç])\1+', r'\1', word.lower()).replace(" ", "")
                if normalized_word in normalized_message:
                    from_user = From(
                        id=message.from_.id,
                        is_bot=message.from_.is_bot,
                        first_name=message.from_.first_name,
                        last_name=message.from_.last_name,
                        username=message.from_.username,
                    )
                    reply_to = ReplyToMessage(
                        message_id=message.message_id,
                        from_=from_user,
                        chat=Chat(id=message.chat.id),
                        text=message.text,
                        photo=message.photo,
                        document=message.document,
                    )
                    mock_message = Message(
                        from_=From(id=0, is_bot=True, first_name="Bot"),
                        chat=Chat(id=message.chat.id),
                        text="/critique",
                        reply_to_message=reply_to,
                        message_id=message.message_id,
                    )
                    await _critic_or_praise(mock_message, telegram, llm, history, user_data)
                    break

async def _critic_or_praise(
        message: Message,
        telegram: Telegram,
        llm: LLM,
        history: ChatHistory,
        user_data: UserDataManager,
) -> None:
    with sending_action(chat_id=message.chat.id, telegram=telegram):
        if not message.reply_to_message or not message.reply_to_message.from_:
            return

        if message.reply_to_message.text:
            text = message.reply_to_message.text
        elif message.reply_to_message.photo:
            text = await get_photo_description(telegram=telegram, llm=llm, message=message.reply_to_message)
        else:
            return

        user_name = message.reply_to_message.from_.first_name
        user_id = message.reply_to_message.from_.id

        target_user = user_data.get_user_data(user_id)
        long_term_opinion = target_user.long_term_opinion if target_user else None

        opinion_prompt = ""

        if message.text.startswith("/critique"):
            prompt = f"Em no máximo 300 caracteres, dê uma bronca dura em {user_name} por ter dito isso: '''{text}'''"
        elif message.text.startswith("/elogie"):
            prompt = f"{'Elogie o' if round(random.random()) else 'Parabenize o'} {user_name} por ter dito isso: " \
                     f"'{text}'"
        elif message.text.startswith("/humilhe"):
            prompt = f"Humilhe {user_name} por ter dito isso: '{text}'"
        else:
            prompt = f"Simpatize com {user_name} por estar nessa situação: '{text}'"

        if long_term_opinion:
            prompt = f"{prompt} levando em consideração o que você sabe sobre ele."
            opinion_prompt = f"\n\nUsando dessa informação que você sabe sobre {user_name}: {long_term_opinion}"

        reply_to = message.reply_to_message.message_id

        prompt = (f"Você é um modelo instruct que deve gerar uma resposta para uma tarefa sem detalhes adicionais e sem questionamentos.\n"
                  f"Você deve gerar uma resposta sem nenhuma informação além da resposta para o que for solicitada, "
                  f"sem dizer coisas como 'aqui vai uma resposta', ou 'se você quiser, posso gerar outra resposta'. "
                  f"O seu objetivo é apenas gerar a resposta final e não conversar.\n\nA tarefa é:{opinion_prompt}\n\n{prompt}")

        for _ in range(5):
            message_text = await llm.generate_text(
                prompt,
                temperature=1,
                model="gpt-5-nano",
                reasoning_effort="low"
            )
            message_text = message_text.lower()

            block_list = ["desculpe,", "não vou", "não posso", "se quiser,", "não acho", "humilhar"]

            if not any(word in message_text for word in block_list):
                break

        if user_name.lower() not in message_text and not message.reply_to_message.from_.is_bot:
            message_text = f"{user_name}, {message_text}"

        if random.random() < 0.25:
            message_text = message_text.upper()

        await telegram.send_message(
            message_text=message_text,
            chat_id=message.chat.id,
            reply_to=reply_to,
        )
