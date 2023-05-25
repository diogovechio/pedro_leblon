import random

import feedparser

from constants.constants import NEWS_WORD_LIST, DRUNK_DECAPTOR_LIST, DECAPTOR_DISAPPOINTS
from data_classes.react_data import ReactData
from utils.text_utils import message_miguxer


async def mock_users(
        data: ReactData
) -> None:
    #Todo: organizar a bagunça
    message = data.message
    bot = data.bot

    user_identified = None

    if message.from_.username in bot.config.mock_messages:
        user_identified = message.from_.username
    elif str(message.from_.id) in bot.config.mock_messages:
        user_identified = str(message.from_.id)

    if (
            user_identified
            and bot.config.mock_messages[user_identified].last_mock_hour != round(bot.datetime_now.hour / 18)
            and random.random() < bot.config.random_params.random_mock_frequency
            and message.chat.id not in bot.config.not_internal_chats
    ):
        bot.loop.create_task(
            bot.send_message(
                message_text=random.choice(bot.config.mock_messages[user_identified].messages),
                chat_id=message.chat.id,
                sleep_time=20 + round(random.random() * 15),
                reply_to=None
            ),
        )

        bot.config.mock_messages[user_identified].last_mock_hour = round(bot.datetime_now.hour / 18)

    if (
            (message.from_.username in ['nands93'])
            and bot.mocked_hour != bot.datetime_now.hour
            and random.random() < bot.config.random_params.words_react_frequency
            and bot.config.rss_feed.news != ""
    ):
        bot.loop.create_task(
            bot.send_message(
                message_text=random.choice(
                    list(
                        filter(
                            lambda url: any(news_word in url for news_word in NEWS_WORD_LIST),
                            [url.link for url in feedparser.parse(bot.config.rss_feed.news).entries]
                        )
                    )
                ),
                chat_id=message.chat.id,
                reply_to=message.message_id,
            )
        )

        bot.mocked_hour = bot.datetime_now.hour

    if (
            user_identified
            and bot.sent_news != round(bot.datetime_now.hour / 6)
            and random.random() < bot.config.random_params.words_react_frequency
            and bot.config.mock_messages[user_identified].rss_feed
            and message.chat.id not in bot.config.not_internal_chats
    ):
        news = [url.link
                for url in feedparser.parse(bot.config.mock_messages[user_identified].rss_feed).entries]

        if len(news):
            bot.loop.create_task(
                bot.send_message(
                    message_text=random.choice(news),
                    chat_id=message.chat.id,
                    sleep_time=30 + (random.random() * 60)
                )
            )

            bot.sent_news = round(bot.datetime_now.hour / 6)

    if message.from_.username == f"{'decaptor' if not bot.debug_mode else 'diogovechio'}":
        if random.random() < bot.config.random_params.random_mock_frequency and not bot.mocked_today:
            bot.loop.create_task(
                bot.send_video(
                    video=open(f'gifs/kardashian{round(random.random())}.mp4', 'rb').read(),
                    chat_id=message.chat.id,
                    reply_to=None,
                    sleep_time=60 + (random.random() * 60)
                ),
            )
            bot.mocked_today = True

        if (
                (bot.datetime_now.hour > 22 or (0 <= bot.datetime_now.hour < 6))
                and random.random() < bot.config.random_params.mock_drunk_decaptor_frequency
        ):
            bot.loop.create_task(
                bot.send_message(
                    message_text=await message_miguxer(message.text) if round(
                        random.random()) else random.choice(DRUNK_DECAPTOR_LIST),
                    chat_id=message.chat.id,
                    reply_to=message.message_id if round(random.random()) else None
                )
            )

        if 'lol' in message.text.lower() and random.random(

        ) < bot.config.random_params.words_react_frequency and not bot.kardashian_gif != round(bot.datetime_now.hour / 18):
            bot.loop.create_task(
                bot.send_video(
                    video=open(f'gifs/kardashian_lol.mp4', 'rb').read(),
                    chat_id=message.chat.id,
                    reply_to=None,
                    sleep_time=10 + (random.random() * 15)
                )
            )
            bot.kardashian_gif = round(bot.datetime_now.hour / 8)

        if any(word in message.text.lower() for word in DECAPTOR_DISAPPOINTS) and not bot.kardashian_gif != round(bot.datetime_now.hour / 18):
            bot.loop.create_task(
                bot.send_video(
                    video=open(f'gifs/kardashian_disappointed.mp4', 'rb').read(),
                    chat_id=message.chat.id,
                    reply_to=None,
                    sleep_time=10 + (random.random() * 15)
                )
            )
            bot.kardashian_gif = round(bot.datetime_now.hour / 18)
