import random

import feedparser

from constants.constants import ASK_PHOTOS
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro


async def words_reactions(
        bot: FakePedro,
        message: TelegramMessage
) -> None:
    if message.text.lower() in ['oi', 'bom dia', 'boa noite', 'adeus', 'rs', 'kk'] or (
            len(
                set(
                    list(message.text.lower())
                    )
                ) <= 2 and len(message.text) > 2 and random.random() < bot.config.random_params.random_mock_frequency
    ):
        bot.loop.create_task(
            bot.send_message(
                message_text=message.text,
                chat_id=message.chat.id)
        )

    if bot.config.ask_photos and any(
            word in message.text.lower() for word in ASK_PHOTOS
    ) and random.random() < bot.config.random_params.words_react_frequency:

        if bot.asked_for_photo != round(bot.datetime_now.hour / 8):

            embeddings_count = {key: bot.faces_names.count(key) for key in bot.faces_names}

            low_photo_count = [key for key, value in embeddings_count.items() if
                               value == embeddings_count[min(embeddings_count, key=embeddings_count.get)]]

            high_photo_count = [key for key, value in embeddings_count.items() if
                                value == embeddings_count[max(embeddings_count, key=embeddings_count.get)]]

            bot.loop.create_task(
                bot.send_message(
                    f"{message.from_.first_name.lower()} manda uma foto do "
                    f"{random.choice(low_photo_count)} {'aí rapidão' if round(random.random()) else 'aí'}, "
                    f"eu ainda nao coheço ele tanto quanto o {random.choice(high_photo_count)}",
                    chat_id=message.chat.id,
                    sleep_time=2 + round(random.random() * 5),
                    reply_to=message.message_id)
            )

            bot.asked_for_photo = round(bot.datetime_now.hour / 8)

    if (
            random.random() < bot.config.random_params.words_react_frequency
            and bot.config.rss_feed.games != ""
            and bot.sent_games_news != round(bot.datetime_now.hour / 4)
            and message.chat.id not in bot.config.not_internal_chats
    ):
        bot.loop.create_task(
            bot.send_message(
                message_text=random.choice(
                    [url.link for url in feedparser.parse(bot.config.rss_feed.games).entries]
                ),
                chat_id=message.chat.id,
                sleep_time=10 + round(random.random() * 5),
            )
        )

        bot.sent_games_news = round(bot.datetime_now.hour / 4)
