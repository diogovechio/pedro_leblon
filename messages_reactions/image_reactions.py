import asyncio
import random

import typing as T

from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.face_utils import faces_coordinates_detector, image_cropper, face_recognizer
from utils.openai_utils import return_dall_e_limit
from utils.roleta_utils import get_roletas_from_pavuna
from utils.text_utils import greeter


async def image_reactions(
        bot: FakePedro,
        message: TelegramMessage,
        method: str,
        always_send_crop: bool = False,
        dall_e: bool = True
) -> None:
    loop = bot.loop

    if image_bytes := await bot.image_downloader(message):
        if faces_coordinates := await faces_coordinates_detector(image_bytes, bot.config.face_classifier.box_min_size):
            bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="upload_photo"))

            if method == 'cropper':
                async def _crop_and_send(img_bytes: bytes, coord: tuple):
                    crop_bytes = await image_cropper(img_bytes, coord)
                    recognized_face = await face_recognizer(
                        crop_image=crop_bytes[0],
                        full_image=img_bytes,
                        faces_embeddings=bot.face_embeddings,
                        faces_names=bot.faces_names,
                        face_tolerance=bot.config.face_classifier.face_tolerance
                    )

                    feedback = await return_dall_e_limit(
                        _id=message.from_.id,
                        limit_per_user=bot.config.openai.dall_e_daily_limit,
                        used_dall_e_today=bot.used_dall_e_today
                    )

                    if recognized_face or always_send_crop:
                        caption = await create_caption(bot=bot, face_recognized=recognized_face)

                        if dall_e and recognized_face is not None and recognized_face[0] == "samuel" and bot.used_dall_e_today.count(message.from_.id) < bot.config.openai.dall_e_daily_limit:
                            image = await bot.openai.edit_image(
                                text="manifestação do partido dos trabalhadores com MST em brasília, muita gente de vermelho segurando bandeiras",
                                square_png=crop_bytes[1]
                            )

                            if image is not None:
                                bot.used_dall_e_today.append(message.from_.id)

                            bot.used_dall_e_today.append(message.from_.id)

                            await bot.send_photo(
                                image=image,
                                chat_id=message.chat.id,
                                caption=caption + "\n" + random.choice(
                                    await get_roletas_from_pavuna(bot, 25)
                                )['text'].lower()
                            )

                        elif dall_e and recognized_face is not None and bot.used_dall_e_today.count(message.from_.id) < bot.config.openai.dall_e_daily_limit:
                            is_flagged, roulette_text = True, ""

                            while is_flagged:
                                roulette_text = random.choice(await get_roletas_from_pavuna(bot, 25))['text']
                                is_flagged, _ = await bot.openai.is_flagged(roulette_text)

                            image = await bot.openai.edit_image(
                                text=roulette_text,
                                square_png=crop_bytes[1]
                            )

                            if image is not None:
                                bot.used_dall_e_today.append(message.from_.id)

                            await bot.send_photo(
                                image=image,
                                chat_id=message.chat.id,
                                caption=roulette_text.lower() + f" - {recognized_face[0]}" + f"\n{feedback}" if recognized_face is not None else None
                            )

                            await greet_user(bot=bot, face_recognized=recognized_face, message=message)

                        else:
                            await bot.send_photo(
                                image=crop_bytes[0],
                                chat_id=message.chat.id,
                                caption=await create_caption(bot=bot, face_recognized=recognized_face)
                            )

                for img_coord in faces_coordinates:
                    loop.create_task(_crop_and_send(image_bytes, img_coord))

                return

            elif method == 'face_classifier':
                if face_recognized := await face_recognizer(
                    image_bytes, image_bytes, bot.face_embeddings, bot.faces_names,
                    bot.config.face_classifier.face_tolerance
                ):
                    await greet_user(bot=bot, face_recognized=face_recognized, message=message)

            else:
                raise NotImplementedError('implementa vc')

            await asyncio.gather(
                *[image_cropper(image_bytes, img_coord)
                  for img_coord in faces_coordinates]
            )


async def greet_user(bot: FakePedro, face_recognized: T.Optional[tuple], message: TelegramMessage):
    bot.loop.create_task(bot.send_action(chat_id=message.chat.id, action="typing"))

    bot.loop.create_task(
        bot.send_message(
            message_text=await bot.openai.generate_message(
                message_text=f"do it in brazillian portuguese: tell {face_recognized[0]} he looks "
                             f"{face_recognized[2]} in this picture, give him a advice about this.",
                temperature=1.0,
                biased=True
            ) if face_recognized[2] else await greeter(
                face_recognized[0],
                face_recognized[1],
                bot.config.face_classifier.face_min_accepted_matches
            ),
            chat_id=message.chat.id,
            reply_to=message.message_id
        )
    )


async def create_caption(bot: FakePedro, face_recognized: T.Optional[tuple]) -> T.Optional[str]:
    caption = None

    if face_recognized:
        caption = await bot.openai.generate_message(
            message_text=f"do it in brazillian portuguese: tell {face_recognized[0]} he looks "
                         f"{face_recognized[2]} in this picture, give him a advice about this.",
            temperature=1.0,
            biased=True
        ) if face_recognized[2] else await greeter(
            face_recognized[0],
            face_recognized[1],
            bot.config.face_classifier.face_min_accepted_matches
        )

    return caption
