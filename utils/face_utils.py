import os
import uuid
import typing as T

import face_recognition
from PIL import Image


async def faces_locator(image: bytes, min_size: int) -> T.Optional[iter]:
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


async def face_cropper(image: bytes, coords: tuple) -> bytes:
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
    return image_bytes


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
            result_name = max(balanced_predict_result, key=balanced_predict_result.get)
            data = result_name, balanced_predict_result[result_name]

    del input_image_embeddings
    os.remove(temp_filename)

    return data
