import random

import feedparser

from constants.constants import ASK_PHOTOS, SWEAR_WORDS
from data_classes.react_data import ReactData
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.roleta_utils import get_roletas_from_pavuna


async def words_reactions(
        data: ReactData
) -> None:
    # Todo: organizar a bagunça
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
                and data.bot.datetime_now.day % 2 == 0
        ):
            data.bot.loop.create_task(
                data.bot.send_message(
                    message_text=(random.choice(await get_roletas_from_pavuna(data.bot)))['text'].lower(),
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
