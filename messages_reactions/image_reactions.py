import asyncio
import random

from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.face_utils import faces_detector, image_cropper, face_classifier
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
        if faces_coordinates := await faces_detector(image_bytes, bot.config.face_classifier.box_min_size):

            if method == 'cropper':
                async def _crop_and_send(img_bytes: bytes, coord: tuple):
                    crop_bytes = await image_cropper(img_bytes, coord)
                    recognized_face = await face_classifier(
                        image=crop_bytes[0],
                        faces_embeddings=bot.face_embeddings,
                        faces_names=bot.faces_names,
                        face_tolerance=bot.config.face_classifier.face_tolerance
                    )

                    if recognized_face or always_send_crop:
                        if dall_e and recognized_face is not None and recognized_face[0] == "samuel":
                            await bot.send_photo(
                                image=await bot.openai.edit_image(
                                    text="manifestação do partido dos trabalhadores com MST em brasília, muita gente de vermelho segurando bandeiras",
                                    square_png=crop_bytes[1]
                                ),
                                chat_id=message.chat.id,
                                caption=await greeter(
                                    recognized_face[0],
                                    recognized_face[1],
                                    bot.config.face_classifier.face_min_accepted_matches
                                ) if recognized_face is not None else None
                            )

                        elif dall_e and recognized_face is not None:
                            is_flagged, roleta_text = True, ""

                            while is_flagged:
                                roleta_text = random.choice(await get_roletas_from_pavuna(bot, 25))['text']
                                is_flagged, _ = await bot.openai.is_flagged(roleta_text)

                            await bot.send_photo(
                                image=await bot.openai.edit_image(
                                    text=roleta_text,
                                    square_png=crop_bytes[1]
                                ),
                                chat_id=message.chat.id,
                                caption=(await greeter(
                                    recognized_face[0],
                                    recognized_face[1],
                                    bot.config.face_classifier.face_min_accepted_matches
                                )) + "\n" + roleta_text.lower() if recognized_face is not None else None
                            )

                        else:
                            await bot.send_photo(
                                image=crop_bytes[0],
                                chat_id=message.chat.id,
                                caption=await greeter(
                                    recognized_face[0],
                                    recognized_face[1],
                                    bot.config.face_classifier.face_min_accepted_matches
                                ) if recognized_face is not None else None
                            )

                for img_coord in faces_coordinates:
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
                *[image_cropper(image_bytes, img_coord)
                  for img_coord in faces_coordinates]
            )
