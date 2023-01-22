import json
import logging
import random
import typing as T

from pedro_leblon import FakePedro


async def get_roletas_from_pavuna(
        bot: FakePedro,
        min_chars=0
) -> T.List[dict]:
    # async with bot.session.get("https://keyo.me/bot/roleta.json") as roleta:
    # return [
    #     value['text'] for _, value in json.loads(
    #         await roleta.content.read()
    #     ).items()
    #     if value['text'] is not None and len(value['text']) > min_chars
    # ]
    with open("new_roletas.json", "rb") as roleta:
        return [
            value for _, value in json.loads(roleta.read()).items()
            if value['text'] is not None and len(value['text']) > min_chars
        ]


def arrombado_classifier(message: dict) -> str:
    try:
        if message['username'] is not None and "staltz" in message['username'].lower():
            return 'staltz'
        if message['sender_name'] is not None and 'andr' in message['sender_name'].lower():
            if message['username'] is None or (message['username'] is not None and message['username'] == 'decaptor'):
                return 'decaptor'
        if (
                (message['sender_name'] is not None and message['sender_name'].lower() == 'sam')
                or
                (message['username'] is not None and message['username'] == 'samzn')
                or
                (message['sender_name'] is not None and message['sender_name'].lower() == 'samuel')
        ):
            return 'samuel'
        if message['sender_name'] is not None and 'deleted' in message['sender_name'].lower():
            return random.choice(
                ['samuel', 'cocao']
            )

        if message['username'] is not None and 'diogovechio' in message['username'].lower():
            return 'diogo'
        if (
                (message['username'] is not None and 'nands93' in message['username'].lower())
                or
                (message['sender_name'] is not None and 'nando' in message['sender_name'].lower())
        ):
            return 'nando'
        if (
                (message['username'] is not None and 'thommazk' in message['username'].lower())
                or
                (message['sender_name'] is not None and 'thomm' in message['sender_name'].lower())
        ):
            return 'thommaz'
        if (
                (message['username'] is not None and 'renfd' in message['username'].lower())
                or
                (message['sender_name'] is not None and 'renat' in message['sender_name'].lower())
        ):
            return 'renato'
        if (
                (message['username'] is not None and 'cocao' in message['username'].lower())
                or
                (message['sender_name'] is not None and 'michae' in message['sender_name'].lower())
                or
                (message['sender_name'] is not None and 'cocao' in message['sender_name'].lower())
        ):
            return 'cocao'
        if (
                (message['username'] is not None and 'guax' in message['username'].lower())
                or
                (message['sender_name'] is not None and 'guax' in message['sender_name'].lower())
        ):
            return 'guaxinim'
        if (
                (message['username'] is not None and 'keyo' in message['username'].lower())
                or
                (message['sender_name'] is not None and 'keyo' in message['sender_name'].lower())
                or
                (message['sender_name'] is not None and 'marco' in message['sender_name'].lower())
        ):
            return 'renato'
        if (
                (message['username'] is not None and 'fabio' in message['username'].lower())
                or
                (message['sender_name'] is not None and 'fabio' in message['sender_name'].lower())
        ):
            return 'fabinho b boy'
        if (
                (message['username'] is not None and 'eicho' in message['username'].lower())
                or
                (message['sender_name'] is not None and 'thiago' in message['sender_name'].lower())
        ):
            return 'eicho'
    except Exception as exc:
        logging.exception(exc)
    return 'pinto e cu'
