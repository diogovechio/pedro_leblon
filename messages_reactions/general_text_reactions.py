import random

import feedparser
from unidecode import unidecode

from constants.constants import ASK_PHOTOS, SWEAR_WORDS
from data_classes.react_data import ReactData
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.roleta_utils import get_roletas_from_pavuna


async def words_reactions(
        data: ReactData
) -> None:
    normalized_input_text = unidecode(data.input_text.lower().strip())
    if (
            (
                data.message.text.lower() in ['oi', 'bom dia', 'boa noite', 'adeus', 'kk'] or (
                    len(
                        set(
                            list(data.message.text.lower())
                        )
                    ) <= 2 < len(data.message.text)
            )
            ) and data.message.chat.id not in data.bot.config.not_internal_chats
    ) and random.random() < data.bot.config.random_params.random_mock_frequency:
        data.bot.loop.create_task(
            data.bot.send_message(
                message_text=data.message.text,
                chat_id=data.message.chat.id)
        )

    if any(
            swear_word in data.message.text.lower() for swear_word in SWEAR_WORDS
    ):
        if (
                random.random() < data.bot.config.random_params.words_react_frequency
                and data.message.chat.id not in data.bot.config.not_internal_chats
        ):
            roletas = await get_roletas_from_pavuna(data.bot, keyo=True)

            chosen_roleta = random.choice(roletas)['text'].lower()

            data.bot.loop.create_task(
                data.bot.send_message(
                    message_text=chosen_roleta,
                    chat_id=data.message.chat.id,
                    sleep_time=2 + round(random.random() * 5)
                )
            )

    if (
            data.bot.config.ask_photos and any(word in data.message.text.lower() for word in ASK_PHOTOS)
            and random.random() < data.bot.config.random_params.words_react_frequency
            and data.message.chat.id not in data.bot.config.not_internal_chats
    ):
        if data.bot.asked_for_photo != round(data.bot.datetime_now.hour / 8):
            embeddings_count = {key: data.bot.faces_names.count(key) for key in data.bot.faces_names}

            low_photo_count = [key for key, value in embeddings_count.items() if
                               value == embeddings_count[min(embeddings_count, key=embeddings_count.get)]]

            high_photo_count = [key for key, value in embeddings_count.items() if
                                value == embeddings_count[max(embeddings_count, key=embeddings_count.get)]]

            data.bot.loop.create_task(
                data.bot.send_message(
                    f"{data.message.from_.first_name.lower()} manda uma foto do "
                    f"{random.choice(low_photo_count)} {'aí rapidão' if round(random.random()) else 'aí'}, "
                    f"eu ainda nao coheço ele tanto quanto o {random.choice(high_photo_count)}",
                    chat_id=data.message.chat.id,
                    sleep_time=2 + round(random.random() * 5),
                    reply_to=data.message.message_id)
            )

            data.bot.asked_for_photo = round(data.bot.datetime_now.hour / 8)

    if (
            random.random() < data.bot.config.random_params.random_mock_frequency and not data.bot.mocked_today
            and data.message.chat.id not in data.bot.config.not_internal_chats
    ) or "xiiii" in data.input_text.lower():
        data.bot.loop.create_task(
            data.bot.set_message_reaction(
                message_id=data.message.message_id,
                chat_id=data.message.chat.id,
                reaction='💩',
            )
        )

        data.bot.mocked_today = True

    if any(
            word == unidecode(data.input_text.lower().strip())
            for word in ["meu deus", "wtf", "pqp", "nossa", "caralho", "vsf", "tnc", "vtnc", "vai tomar no cu"]
    ):
        data.bot.loop.create_task(
            data.bot.set_message_reaction(
                message_id=data.message.message_id,
                chat_id=data.message.chat.id,
                reaction=random.choice(["😱", "😨"]),
            )
        )

    if any(word in data.input_text.lower() for word in
           ["governo", "lula", "faz o l", "china", "bostil", "lixo de pa", "imposto", "bolsonaro", "trump", "milei"]
           ) and data.message.from_.username and any(user in data.message.from_.username for user in ["decaptor", "nands93"]):
        data.bot.loop.create_task(
            data.bot.set_message_reaction(
                message_id=data.message.message_id,
                chat_id=data.message.chat.id,
                reaction=random.choice(["💩", "🤡", "🤪"]),
            )
        )

    if any(word in unidecode(data.input_text.lower()) for word in ["parabens", "muito bom", "otimo", "excelente"]):
        data.bot.loop.create_task(
            data.bot.set_message_reaction(
                message_id=data.message.message_id,
                chat_id=data.message.chat.id,
                reaction=random.choice(["🎉", "👏", "🏆", "🍾", "❤", "💯"]),
            )
        )

    if "bom dia" in unidecode(data.input_text.lower()) and data.bot.mocked_hour != data.bot.datetime_now.hour:
        data.bot.loop.create_task(
            data.bot.set_message_reaction(
                message_id=data.message.message_id,
                chat_id=data.message.chat.id,
                reaction='❤',
            )
        )

        data.bot.mocked_hour = data.bot.datetime_now.hour

    if any(word in unidecode(data.input_text.lower()) for word in ["viado", "bicha", "gay"]) and "enviado" not in data.input_text.lower():
        data.bot.loop.create_task(
            data.bot.set_message_reaction(
                message_id=data.message.message_id,
                chat_id=data.message.chat.id,
                reaction=random.choice(["💅", "🦄", "🌭", "👀", "🌚"]),
            )
        )

    if (
            random.random() < data.bot.config.random_params.words_react_frequency
            and data.bot.config.rss_feed.games != ""
            and data.bot.sent_news != round(data.bot.datetime_now.hour / 6)
            and data.message.chat.id not in data.bot.config.not_internal_chats
    ):
        data.bot.loop.create_task(
            data.bot.send_message(
                message_text=random.choice(
                    [url.link for url in feedparser.parse(data.bot.config.rss_feed.games).entries]
                ),
                chat_id=data.message.chat.id,
                sleep_time=30 + (random.random() * 60)
            )
        )

        data.bot.sent_news = round(data.bot.datetime_now.hour / 6)
