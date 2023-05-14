import asyncio
import random

import typing as T

from data_classes.image_data import FaceResult
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.face_utils import faces_coordinates_detector, image_cropper, detect_face
from utils.logging_utils import async_elapsed_time
from utils.openai_utils import return_dall_e_limit
from utils.roleta_utils import get_roletas_from_pavuna
from utils.text_utils import greeter


@async_elapsed_time
async def image_reactions(
        bot: FakePedro,
        message: TelegramMessage,
        method: str,
        always_send_crop: bool = False
) -> None:
    loop = bot.loop

    if image_bytes := await bot.image_downloader(message):
        if faces_coordinates := await faces_coordinates_detector(image_bytes, bot.config.face_classifier.box_min_size):
            with bot.sending_action(message.chat.id, action="upload_photo"):
                if method == 'cropper':
                    @async_elapsed_time
                    async def _crop_and_send(img_bytes: bytes, coord: tuple):
                        crop_bytes = await image_cropper(img_bytes, coord)
                        recognized_face = await detect_face(
                            crop_image=crop_bytes.original_face,
                            full_image=img_bytes,
                            faces_embeddings=bot.face_embeddings,
                            faces_names=bot.faces_names,
                            face_tolerance=bot.config.face_classifier.face_tolerance
                        )

                        feedback = await return_dall_e_limit(
                            id_to_count=message.from_.id,
                            limit_per_user=bot.config.openai.dall_e_daily_limit,
                            dall_uses_list=bot.dall_e_uses_today
                        )

                        if recognized_face or always_send_crop:
                            caption: str
                            image: T.Optional[bytes] = None

                            if (
                                    recognized_face is not None and recognized_face.face_name == "samuel"
                                    and bot.dall_e_uses_today.count(message.from_.id) < bot.config.openai.dall_e_daily_limit
                            ):

                                caption, image = await asyncio.gather(
                                    create_caption(
                                        bot=bot,
                                        face_data=recognized_face
                                    ),
                                    bot.openai.edit_image(
                                        text="manifestação do partido dos trabalhadores com MST em brasília, "
                                             "muita gente de vermelho segurando bandeiras",
                                        square_png=crop_bytes.face_with_alpha_background
                                    )
                                )

                                await bot.send_photo(
                                    image=image,
                                    chat_id=message.chat.id,
                                    caption=caption + "\n" + random.choice(
                                        await get_roletas_from_pavuna(bot, 25)
                                    )['text'].lower()
                                )

                            elif (
                                    recognized_face is not None and
                                    bot.dall_e_uses_today.count(message.from_.id) < bot.config.openai.dall_e_daily_limit
                            ):
                                is_flagged, roulette_text = True, ""

                                while is_flagged:
                                    roulette_text = random.choice(await get_roletas_from_pavuna(bot, 25))['text']
                                    is_flagged, _ = await bot.openai.is_flagged(roulette_text)

                                image = await bot.openai.edit_image(
                                    text=roulette_text,
                                    square_png=crop_bytes.face_with_alpha_background
                                )


                                await bot.send_photo(
                                    image=image,
                                    chat_id=message.chat.id,
                                    caption=roulette_text.lower() + f" - {recognized_face.face_name}" + f"\n{feedback}"
                                        if recognized_face is not None else None
                                )

                                await greet_user(bot=bot, face_recognized=recognized_face, message=message)

                            else:
                                await bot.send_photo(
                                    image=crop_bytes.original_face,
                                    chat_id=message.chat.id,
                                    caption=await create_caption(bot=bot, face_data=recognized_face)
                                )

                            if image is not None:
                                bot.dall_e_uses_today.append(message.from_.id)

                    for img_coord in faces_coordinates:
                        loop.create_task(
                            _crop_and_send(img_bytes=image_bytes, coord=img_coord)
                        )

                    return

                elif method == 'face_classifier':
                    if face_recognized := await detect_face(
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


async def greet_user(
        bot: FakePedro,
        face_recognized: T.Optional[FaceResult],
        message: TelegramMessage
) -> None:
    with bot.sending_action(message.chat.id, action="typing"):
        bot.loop.create_task(
            bot.send_message(
                message_text=await create_caption(
                    bot=bot,
                    face_data=face_recognized
                ),
                chat_id=message.chat.id,
                reply_to=message.message_id
            )
        )


async def create_caption(
        bot: FakePedro,
        face_data: T.Optional[FaceResult],
) -> T.Optional[str]:
    caption = None

    if face_data:
        caption = await bot.openai.generate_message(
            full_text=f"considerando que você é o pedro, diga ao {face_data.face_name} que você achou ele "
                         f"{face_data.emotion} nessa foto. faça um comentário sobre a foto.\n\npedro:",
            temperature=1.0,
            biased=True
        ) if face_data.emotion else await greeter(
            name=face_data.face_name,
            match_result=face_data.match_result,
            min_accepted_matches=bot.config.face_classifier.face_min_accepted_matches
        )

        caption = (caption.lower()).replace('"',"")

    return caption
