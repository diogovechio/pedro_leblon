import random

import feedparser

from constants.constants import NEWS_WORD_LIST, DRUNK_DECAPTOR_LIST, DECAPTOR_DISAPPOINTS
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.text_utils import message_miguxer


async def mock_users(
        bot: FakePedro,
        message: TelegramMessage,
        from_samuel: bool,
        from_debug_chats: bool
) -> None:
    if message.from_.username in bot.config.mock_messages:
        if bot.config.mock_messages[message.from_.username].last_mock_hour != bot.datetime_now.hour:
            if random.random() < bot.config.random_params.random_mock_frequency:
                bot.loop.create_task(
                    bot.send_message(
                        message_text=random.choice(bot.config.mock_messages[message.from_.username].messages),
                        chat_id=message.chat.id,
                        sleep_time=2 + round(random.random() * 5),
                        reply_to=None),
                )
                bot.config.mock_messages[message.from_.username].last_mock_hour = bot.datetime_now.hour

    if (
            (message.from_.username in ['nands93', 'theyuush'] or from_debug_chats)
            and bot.sent_news != bot.datetime_now.hour
            and random.random() < bot.config.random_params.random_mock_frequency
    ):
        bot.loop.create_task(
            bot.send_message(
                message_text=random.choice(
                    list(
                        filter(
                            lambda url: any(news_word in url for news_word in NEWS_WORD_LIST),
                            [url.link for url in feedparser.parse(bot.config.rss_feed.url).entries]
                        )
                    )
                ),
                chat_id=message.chat.id,
                reply_to=message.message_id
            )
        )
        bot.sent_news = bot.datetime_now.hour

    if message.from_.username == f"{'decaptor' if not bot.debug_mode else 'diogovechio'}":

        if random.random() < bot.config.random_params.random_mock_frequency:
            bot.loop.create_task(
                bot.send_video(
                    video=open(f'gifs/kardashian{round(random.random())}.mp4', 'rb').read(),
                    chat_id=message.chat.id,
                    reply_to=message.message_id),
            )

        if bot.datetime_now.hour > 21 or (0 <= bot.datetime_now.hour < 6):
            if random.random() < bot.config.random_params.mock_drunk_decaptor_frequency:
                bot.loop.create_task(
                    bot.send_message(
                        message_text=await message_miguxer(message.text) if round(
                            random.random()) else random.choice(DRUNK_DECAPTOR_LIST),
                        chat_id=message.chat.id,
                        reply_to=message.message_id if round(random.random()) else None),
                )

        if 'lol' in message.text.lower() and random.random() < bot.config.random_params.words_react_frequency:
            bot.loop.create_task(
                bot.send_video(
                    video=open(f'gifs/kardashian_lol.mp4', 'rb').read(),
                    chat_id=message.chat.id,
                    reply_to=None)
            )

        if any(word in message.text.lower() for word in DECAPTOR_DISAPPOINTS):
            bot.loop.create_task(
                bot.send_video(
                    video=open(f'gifs/kardashian_disappointed.mp4', 'rb').read(),
                    chat_id=message.chat.id,
                    reply_to=message.message_id),
            )
            bot.config.mock_messages[message.from_.username].last_mock_hour = bot.datetime_now.hour
