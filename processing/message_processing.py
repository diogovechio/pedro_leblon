import asyncio
import feedparser

from constants.constants import drunk_decaptor_taunt_list, swear_words, ask_photos, cocao_list
import random

from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.face_utils import face_cropper, face_classifier, faces_locator
from utils.text_utils import message_miguxer, greeter


async def message_processing(
        bot: FakePedro,
        message: TelegramMessage
) -> None:
    if message.chat.id in bot.allowed_list:
        from_samuel = message.from_.is_premium
        from_debug_chats = message.chat.id in (-20341310, 8375482)

        if message.photo:
            bot.loop.create_task(
                image_pipeline(
                    bot=bot,
                    message=message,
                    method='cropper' if from_samuel or from_debug_chats else 'face_classifier'
                )
            )
        if message.text:
            if message.from_.username in ['nands93', 'theyuush'] or from_samuel or from_debug_chats:
                if bot.sent_news != bot.datetime_now.hour:
                    if random.random() < bot.config.random_params.random_mock_frequency:
                        bot.loop.create_task(
                            bot.send_message(
                                message_text=random.choice(
                                    [url.link for url in feedparser.parse(bot.config.rss_feed.url).entries]),
                                chat_id=message.chat.id,
                                reply_to=message.message_id
                            )
                        )
                        bot.sent_news = bot.datetime_now.hour
            if message.from_.username in bot.config.mock_messages:
                if bot.config.mock_messages[message.from_.username].lastmock != bot.datetime_now.hour:
                    if random.random() < bot.config.random_params.random_mock_frequency:
                        bot.loop.create_task(
                            bot.send_message(
                                message_text=random.choice(bot.config.mock_messages[message.from_.username].messages),
                                chat_id=message.chat.id,
                                sleep_time=2 + round(random.random() * 5),
                                reply_to=None),
                        )
                        bot.config.mock_messages[message.from_.username].lastmock = bot.datetime_now.hour
            if message.from_.username == 'decaptor':
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
                for word in swear_words:
                    if word in message.text.lower() and random.random() < bot.config.random_params.words_react_frequency:
                        bot.loop.create_task(
                            bot.send_video(
                                video=open(f'gifs/nossa.mp4', 'rb').read(),
                                chat_id=message.chat.id,
                                reply_to=None)
                        )
                        break
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
            if message.text == '/andrebebado' and message.from_.username != 'decaptor' and not from_samuel:
                bot.config.random_params.mock_drunk_decaptor_frequency = 1.0
                bot.loop.create_task(bot.send_message(
                    message_text='Modo André Bêbado ativado',
                    chat_id=message.from_.id)
                )
            if message.text == '/andresobrio' and message.from_.username != 'decaptor' and not from_samuel:
                bot.config.random_params.mock_drunk_decaptor_frequency = 0.0
                bot.loop.create_task(bot.send_message(
                    message_text='Modo André Sóbrio ativado',
                    chat_id=message.from_.id)
                )
            if message.text == '/reload' and message.from_.username == 'diogovechio':
                await bot.send_message(
                    message_text='Recarregando parâmetros',
                    chat_id=message.chat.id
                )
                await bot.load_config_params()
                embeddings_count = {key: bot.faces_names.count(key) for key in bot.faces_names}
                bot.loop.create_task(bot.send_message(
                    message_text=f"{bot.config.random_params}\n"
                        f"IDS: {bot.allowed_list}\n"
                        f"{bot.config.face_classifier}\n"
                        f"{bot.config.rss_feed}\n\n"
                        f"Total de fotos:\n{embeddings_count}"
                    ,
                    chat_id=message.chat.id)
                )


async def image_pipeline(
        bot: FakePedro,
        message: TelegramMessage,
        method: str
):
    loop = bot.loop

    if image_bytes := await bot.image_downloader(message):
        if face_coords := await faces_locator(image_bytes, bot.config.face_classifier.box_min_size):
            if method == 'cropper':
                async def _crop_and_send(img_bytes: bytes, coord: tuple):
                    crop_bytes = await face_cropper(img_bytes, coord)
                    recognized_face = await face_classifier(
                        image=crop_bytes,
                        faces_embeddings=bot.face_embeddings,
                        faces_names=bot.faces_names,
                        face_tolerance=bot.config.face_classifier.face_tolerance
                    )
                    await bot.send_photo(
                        image=crop_bytes,
                        chat_id=message.chat.id,
                        caption=await greeter(
                            recognized_face[0],
                            recognized_face[1],
                            bot.config.face_classifier.face_min_accepted_matches
                        ) if recognized_face is not None else None
                    )

                for img_coord in face_coords:
                    loop.create_task(_crop_and_send(image_bytes, img_coord))
                return
            elif method == 'face_classifier':
                if face_recognized := await face_classifier(
                        image_bytes, bot.face_embeddings, bot.faces_names,
                        bot.config.face_classifier.face_tolerance):
                    loop.create_task(
                        bot.send_message(
                            message_text=await greeter(
                                face_recognized[0],
                                face_recognized[1],
                                bot.config.face_classifier.face_min_accepted_matches
                            ),
                            chat_id=message.chat.id)
                    )
            else:
                raise NotImplementedError('implementa vc')

            await asyncio.gather(
                *[face_cropper(image_bytes, img_coord)
                  for img_coord in face_coords]
            )
