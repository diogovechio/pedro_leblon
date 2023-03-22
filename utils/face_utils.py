import os
import random
import uuid
import typing as T
from asyncio import get_running_loop

import face_recognition
from deepface import DeepFace

from PIL import Image, ImageOps

from pedro_leblon import FakePedro, telegram_logging


async def faces_coordinates_detector(image: bytes, min_size: int) -> T.Optional[T.List[T.Tuple]]:
    temp_filename = f'tmp/{uuid.uuid4()}.tmp'
    with open(temp_filename, 'wb') as file:
        file.write(image)
    file = face_recognition.load_image_file(temp_filename)
    faces_location = face_recognition.face_locations(file)
    del file
    os.remove(temp_filename)
    filtered_by_size = [coord for coord in faces_location
                        if (coord[2] - coord[0] + coord[1] - coord[3]) / 2 >= min_size]
    if len(filtered_by_size):
        return filtered_by_size


async def image_cropper(image: bytes, coords: tuple) -> T.Tuple[bytes, bytes]:
    temp_load = f'tmp/{uuid.uuid4()}.tmp'
    with open(temp_load, 'wb') as file:
        file.write(image)
    img = Image.open(temp_load)
    img = img.crop((coords[3], coords[0], coords[1], coords[2]))
    temp_save = f'face_lake/{uuid.uuid4()}.jpg'
    img.save(temp_save)
    with open(temp_save, 'rb') as file:
        image_crop = file.read()
    del img
    os.remove(temp_load)
    image_with_alpha_background = await put_face_on_background(image_crop)
    return image_crop, image_with_alpha_background

async def put_face_on_background(image: bytes, small_face=False) -> bytes:
    background = Image.open("static/background.png")
    temp_load = f'tmp/{uuid.uuid4()}.tmp'
    with open(temp_load, 'wb') as file:
        file.write(image)
    face = Image.open(temp_load)

    if not small_face:
        random_size = round(100 + 125 * random.random())
        random_posx = round(0 + 300 * random.random())
        random_posy = round(0 + 300 * random.random())
    else:
        random_size = round(60 + 40 * random.random())
        random_posx = round(0 + 300 * random.random())
        random_posy = round(0 + 120 * random.random())

    face = ImageOps.contain(face, (random_size , random_size))

    background = background.convert('RGBA')
    face = face.convert('RGBA')

    background.paste(face, (random_posx, random_posy), face)

    temp_save = f'tmp/{uuid.uuid4()}.png'
    background.save(temp_save)

    file_bytes: bytes

    with open(temp_save, 'rb') as file:
        file_bytes = file.read()

    del background, face
    os.remove(temp_save)
    os.remove(temp_load)

    return file_bytes

async def put_list_of_faces_on_background(bot: FakePedro, names: T.List[str], small_face=False) -> bytes:
    background = Image.open("static/background.png")
    background = background.convert('RGBA')

    random_size = round(120 + 25 * random.random())
    random_posx = round(10 + 5 * random.random())

    for i, name in enumerate(names):
        random_posy = round(5 + 130 * random.random())

        if i == 2:
            random_size = round(175 + 25 * random.random())
            random_posx = 125
            random_size += 20
        if i >= 2:
            random_posy = 270

        alpha_faces_list = [file_name for file_name in bot.alpha_faces_files if name in file_name]
        regular_faces_list = [file_name for file_name in bot.faces_files if name in file_name]

        if len(alpha_faces_list):
            random_file_choice = random.choice(alpha_faces_list)
            faces_dir = "faces_alpha"
        else:
            random_file_choice = random.choice(regular_faces_list)
            faces_dir = "faces"

        face_file = f"{faces_dir}/{random_file_choice}"

        if len(names) == 1:
            with open(f"faces/{random.choice(regular_faces_list)}", "rb") as single_face:
                return await put_face_on_background(single_face.read(), small_face)

        face = Image.open(face_file)
        face = ImageOps.contain(face, (random_size, random_size))
        face = face.convert('RGBA')

        background.paste(face, (random_posx, random_posy), face)

        random_posx += round(225 + 25 * random.random())

    temp_save = f'tmp/{uuid.uuid4()}.png'
    background.save(temp_save)

    file_bytes: bytes

    with open(temp_save, 'rb') as file:
        file_bytes = file.read()

    del background
    os.remove(temp_save)

    return file_bytes


async def face_recognizer(
        crop_image: bytes,
        full_image: bytes,
        faces_embeddings: list,
        faces_names: list,
        face_tolerance=0.6
) -> T.Optional[T.Tuple[str, float, str]]:
    temp_filename = f'tmp/{uuid.uuid4()}.png'
    temp_filename_2 = f'tmp/{uuid.uuid4()}.png'
    with open(temp_filename, 'wb') as file:
        file.write(crop_image)

    faces_result = {key: 0 for key in faces_names}

    input_image_embeddings = face_recognition.face_encodings(face_recognition.load_image_file(temp_filename))
    data = None

    emotion = await face_emotion(temp_filename)
    if not emotion:
        with open(temp_filename_2, 'wb') as file:
            file.write(full_image)

        emotion = await face_emotion(temp_filename_2)

    if len(input_image_embeddings):
        results = face_recognition.compare_faces(
            known_face_encodings=[*faces_embeddings],
            face_encoding_to_check=input_image_embeddings[0],
            tolerance=face_tolerance
        )

        valid_result = False
        for idx, result in enumerate(results):
            if result:
                faces_result[faces_names[idx]] += 1
                valid_result = True

        images_count = {key: faces_names.count(key) for key in faces_names}
        balanced_predict_result = {key: value / images_count[key] for key, value in faces_result.items()}

        if valid_result and len(balanced_predict_result):
            result_name: str = max(balanced_predict_result, key=balanced_predict_result.get)
            data = result_name, balanced_predict_result[result_name], emotion

    del input_image_embeddings
    os.remove(temp_filename)

    try:
        os.remove(temp_filename_2)
    except Exception as exc:
        get_running_loop().create_task(telegram_logging(exc))

    return data


async def face_emotion(img_path: str) -> str:
    emotion = ''
    try:
        emotion = DeepFace.analyze(img_path=img_path, actions="emotion")[0]['dominant_emotion']
    finally:
        return emotion
