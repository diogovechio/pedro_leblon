import os
import random
import uuid
import typing as T

import face_recognition
from PIL import Image, ImageOps


async def faces_detector(image: bytes, min_size: int) -> T.Optional[T.List[T.Tuple]]:
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
        image_bytes = file.read()
    del img
    os.remove(temp_load)
    background_img = await put_face_on_background(image_bytes)
    return image_bytes, background_img

async def put_face_on_background(image: bytes) -> bytes:
    background = Image.open("static/background.png")
    temp_load = f'tmp/{uuid.uuid4()}.tmp'
    with open(temp_load, 'wb') as file:
        file.write(image)
    face = Image.open(temp_load)

    random_size = round(100 + 100 * random.random())
    random_posx = round(0 + 250 * random.random())
    random_posy = round(0 + 250 * random.random())

    face = ImageOps.contain(face, (random_size , random_size))

    background = background.convert('RGBA')
    face = face.convert('RGBA')

    background.paste(face, (random_posx, random_posy), face)

    temp_save = f'tmp/{uuid.uuid4()}.png'
    background.save(temp_save)

    with open(temp_save, 'rb') as file:
        return file.read()

async def face_classifier(
        image: bytes,
        faces_embeddings: list,
        faces_names: list,
        face_tolerance=0.6
) -> T.Optional[T.Tuple[str, float]]:
    temp_filename = f'tmp/{uuid.uuid4()}.tmp'
    with open(temp_filename, 'wb') as file:
        file.write(image)

    faces_result = {key: 0 for key in faces_names}

    input_image_embeddings = face_recognition.face_encodings(face_recognition.load_image_file(temp_filename))
    data = None

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
            data = result_name, balanced_predict_result[result_name]

    del input_image_embeddings
    os.remove(temp_filename)

    return data
