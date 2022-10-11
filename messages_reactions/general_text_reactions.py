import random

import feedparser

from constants.constants import ask_photos, openai_block_words, drunk_decaptor_taunt_list
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.text_utils import message_miguxer


async def words_reactions(
        bot: FakePedro,
        message: TelegramMessage
) -> None:
    if message.text.lower() in ['oi', 'bom dia', 'boa noite', 'adeus', 'rs', 'kk'] or (
            len(set(list(message.text.lower()))) <= 2 and len(
        message.text) > 2 and random.random() < bot.config.random_params.words_react_frequency):
        bot.loop.create_task(
            bot.send_message(
                message_text=message.text,
                chat_id=message.chat.id)
        )

    for word in ask_photos:
        if word in message.text.lower() and random.random() < bot.config.random_params.words_react_frequency:
            if bot.asked_for_photo != round(bot.datetime_now.hour / 8):
                embeddings_count = {key: bot.faces_names.count(key) for key in bot.faces_names}
                low_photo_count = [key for key, value in embeddings_count.items() if
                                   value == embeddings_count[min(embeddings_count, key=embeddings_count.get)]]
                high_photo_count = [key for key, value in embeddings_count.items() if
                                    value == embeddings_count[max(embeddings_count, key=embeddings_count.get)]]
                bot.loop.create_task(
                    bot.send_message(
                        message_text=f"{message.from_.first_name.lower()} manda uma foto do "
                                     f"{random.choice(low_photo_count)} {'aí rapidão' if round(random.random()) else 'aí'}, "
                                     f"eu ainda nao coheço ele tanto quanto o {random.choice(high_photo_count)}",
                        chat_id=message.chat.id,
                        sleep_time=2 + round(random.random() * 5),
                        reply_to=message.message_id)
                )
                bot.asked_for_photo = round(bot.datetime_now.hour / 8)
            break


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

    if message.from_.username in ['nands93', 'theyuush'] or from_debug_chats:
        if bot.sent_news != bot.datetime_now.hour:
            if random.random() < bot.config.random_params.random_mock_frequency:
                bot.loop.create_task(
                    bot.send_message(
                        message_text=random.choice(
                            list(
                                filter(
                                    lambda url: (
                                            'lula' in url or 'bolsonaro' in url or 'moro' in url or 'turno' in url or
                                            'dilma' in url or 'pt' in url
                                    ),
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
                            random.random()) else random.choice(drunk_decaptor_taunt_list),
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
        if random.random() < bot.config.random_params.words_react_frequency:
            if bot.config.mock_messages[message.from_.username].last_mock_hour != bot.datetime_now.hour:
                for word in openai_block_words:
                    if word in message.text.lower():
                        bot.loop.create_task(
                            bot.send_video(
                                video=open(f'gifs/nossa.mp4', 'rb').read(),
                                chat_id=message.chat.id,
                                reply_to=None)
                        )
                        bot.config.mock_messages[message.from_.username].last_mock_hour = bot.datetime_now.hour
                        break
                    elif 'lula' in message.text.lower():
                        bot.loop.create_task(
                            bot.send_video(
                                video=open(f'gifs/kardashian_disappointed.mp4', 'rb').read(),
                                chat_id=message.chat.id,
                                reply_to=message.message_id),
                        )
                        bot.config.mock_messages[message.from_.username].last_mock_hour = bot.datetime_now.hour
                        break
