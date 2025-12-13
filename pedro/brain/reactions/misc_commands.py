# Internal
import json
import logging
import random

# Project
from pedro.__version__ import __version__
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.feedback import sending_action
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.data_structures.telegram_message import Message
from pedro.utils.text_utils import create_username

logger = logging.getLogger(__name__)

# Constants
MAX_SENTIMENT = 10


async def misc_commands_reaction(
        message: Message,
        history: ChatHistory,
        telegram: Telegram,
        user_data: UserDataManager,
        llm: LLM,
) -> None:
    if message.text:
        if message.text.startswith("/me"):
            await handle_me_command(message, telegram, user_data, llm)
        elif message.text.startswith('/del') and message.reply_to_message:
            await handle_del_command(message, telegram, llm)
        elif message.text.startswith('/data'):
            await handle_data_command(telegram)
        elif message.text.startswith('/puto'):
            await handle_puto_command(message, telegram, user_data, llm)
        elif message.text.startswith('/version'):
            await handle_version_command(message, telegram)


async def handle_me_command(
    message: Message,
    telegram: Telegram,
    user_data: UserDataManager,
    llm: LLM = None,
) -> None:
    """Handle the /me command, showing user ID, chat ID, and sentiment score."""
    user_sentiment = 0
    user_opinions = []

    # Use user info from reply_to_message if it exists, otherwise use the message sender
    user_info = message.reply_to_message.from_ if message.reply_to_message else message.from_

    username = create_username(user_info.first_name, user_info.username)
    for user_opinion in user_data.get_all_user_opinions():
        user_name = create_username(user_opinion.first_name, user_opinion.username)
        if username == user_name:
            user_sentiment = round(user_opinion.relationship_sentiment, 2)
            user_opinions = user_opinion.opinions

    opinion_message = "Nada."
    if user_opinions and llm:
        opinions_text = "\n- ".join(user_opinions)
        prompt = (f"Com base nas seguintes informações sobre {username}:\n- {opinions_text}\n\n"
                  f"Diga a ele, em uma frase curta (máximo 10 palavras), o que você pensa ou sabe sobre ele.")

        opinion_message = (await llm.generate_text(
            prompt=prompt,
            temperature=1.0,
            model="gpt-4.1-mini"
        )).replace("\n", "")

    await telegram.send_message(
        message_text=f"*ID:* `{user_info.id}`\n"
                     f"*Chat ID:* `{message.chat.id}`\n"
                     f"*Meu ódio por você:* `{user_sentiment}`\n"
                     f"*O que penso e sei sobre você:* `{opinion_message}`",
        chat_id=message.chat.id,
        reply_to=message.message_id,
        parse_mode="Markdown"
    )


async def handle_del_command(
    message: Message,
    telegram: Telegram,
    llm: LLM,
) -> None:
    """Handle the /del command, which deletes messages or responds with criticism."""
    if message.reply_to_message.from_.username is None:
        message.reply_to_message.from_.username = ""

    if (
            message.reply_to_message.from_.id == message.from_.id
            or "pedroleblon" in message.reply_to_message.from_.username
            or message.reply_to_message.from_.is_bot
    ):
        await telegram.delete_message(
            chat_id=message.chat.id,
            message_id=message.reply_to_message.message_id
        )

        await telegram.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )

        # Log the deletion
        logger.info(f"{message.from_.first_name},{message.text},{message.reply_to_message.text}")
    else:
        with sending_action(chat_id=message.chat.id, telegram=telegram, user=message.from_.username):
            from_username = create_username(
                first_name=message.from_.first_name,
                username=message.from_.username
            )
            reply_username = create_username(
                first_name=message.reply_to_message.from_.first_name,
                username=message.reply_to_message.from_.username
            )

            response = await llm.generate_text(
                f'critique duramente o '
                f'{from_username} '
                f'por ter tentado deletar a mensagem "{message.reply_to_message.text}" enviada por'
                f" {reply_username}. 'diga que pretende baní-lo do {message.chat.title}.\n\n"
                f"pedro:",
                temperature=1,
                model="gpt-3.5-turbo-instruct"
            )

            await telegram.send_message(
                message_text=response.upper(),
                chat_id=message.chat.id,
                reply_to=message.message_id,
            )


async def handle_data_command(
    telegram: Telegram,
) -> None:
    """Handle the /data command, sending database content to a specific chat."""
    with open("database/pedro_database.json", "r", encoding="utf-8") as f:
        db_content = json.load(f)

    await telegram.send_document(
        document=json.dumps(db_content, indent=4).encode("utf-8"),
        chat_id=8375482,
        caption="DB",
        file_name="database.json"
    )


async def handle_version_command(
    message: Message,
    telegram: Telegram,
) -> None:
    """Handle the /version command, displaying the bot's version information."""
    await telegram.send_message(
        message_text=f"*Pedro Bot v{__version__}*\n"
                     f"Running the latest and greatest version of Pedro Bot.",
        chat_id=message.chat.id,
        reply_to=message.message_id,
        parse_mode="Markdown"
    )


async def handle_puto_command(
    message: Message,
    telegram: Telegram,
    user_data: UserDataManager,
    llm: LLM,
) -> None:
    # Use user info from reply_to_message if it exists, otherwise use the message sender
    user_info = message.reply_to_message.from_ if message.reply_to_message else message.from_

    username = create_username(user_info.first_name, user_info.username)

    # Get user sentiment
    user_sentiment = 0
    for user_opinion in user_data.get_all_user_opinions():
        user_name = create_username(user_opinion.first_name, user_opinion.username)
        if username == user_name:
            user_sentiment = round(user_opinion.relationship_sentiment, 2)

    if user_sentiment < 0:
        user_sentiment = 0

    with sending_action(chat_id=message.chat.id, telegram=telegram, user=message.from_.username):
        prompt = f"considere que você é o pedro.\nem uma escala de 0 a {MAX_SENTIMENT}, " \
                 f"onde:\n" \
                 f"0 = extremamente contente, melhores amigos\n" \
                 f"1 = contente" \
                 f"\n...\n" \
                 f"5 = neutro" \
                 f"\n...\n" \
                 f"{MAX_SENTIMENT - 1} = puto" \
                 f"\n{MAX_SENTIMENT} = extremamente puto:\n"

        if message.text.startswith('/putos'):
            persons = ""
            for user_opinion in user_data.get_all_user_opinions():
                sentiment = user_opinion.relationship_sentiment
                if sentiment > 2:
                    user_name = create_username(user_opinion.first_name, user_opinion.username)
                    persons += f"{user_name.split(' ')[0]}: {int(sentiment)}\n"

            if persons:
                prompt += f"temos as seguintes pessoas seguidas da escala do quanto você está puto com elas:\n\n{persons}\n\n" \
                          f"descreva de maneira como você, pedro, se sente com cada uma dessas pessoas, sem dizer o valor da escala. " \
                          f"reclame grosseiramente com aqueles que te deixaram puto, lembrando de alguma situação que essa pessoa fez com você.\npedro:"
            else:
                prompt = "diga que não está irritado com ninguém.\npedro:"
        else:
            prompt += f"temos o seguinte valor:\n\n{user_sentiment}\n\nentão, dentro da escala, " \
                 f"diga para o {username} o quanto você " \
                 f"está contente ou puto com ele. sem dizer exatamente os valores e nem revelar a escala." \
                 f"\n{'dê um exemplo de como você se sente com isso.' if round(random.random()) else 'faça uma curta poesia sobre isso.'}\n\n" \
                 f"\npedro:"

        response = await llm.generate_text(
            prompt,
            temperature=1,
            model="gpt-3.5-turbo-instruct"
        )

        await telegram.send_message(
            message_text=response.lower(),
            chat_id=message.chat.id,
            reply_to=message.message_id,
        )
