import asyncio
import typing as T

from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.face_utils import faces_detector, image_cropper, face_classifier
from utils.text_utils import greeter


async def image_reactions(
        bot: FakePedro,
        message: TelegramMessage,
        method: str,
        always_send_crop: bool = False
) -> None:
    loop = bot.loop

    if image_bytes := await bot.image_downloader(message):
        if face_coords := await faces_detector(image_bytes, bot.config.face_classifier.box_min_size):

            if method == 'cropper':
                async def _crop_and_send(img_bytes: bytes, coord: tuple):
                    crop_bytes = await image_cropper(img_bytes, coord)
                    recognized_face = await face_classifier(
                        image=crop_bytes,
                        faces_embeddings=bot.face_embeddings,
                        faces_names=bot.faces_names,
                        face_tolerance=bot.config.face_classifier.face_tolerance
                    )

                    if recognized_face or always_send_crop:
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
                *[image_cropper(image_bytes, img_coord)
                  for img_coord in face_coords]
            )
