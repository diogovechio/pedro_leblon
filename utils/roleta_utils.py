import json

from pedro_leblon import FakePedro


async def get_roletas_from_pavuna(
        bot: FakePedro,
        min_chars=0
) -> list[str]:
    async with bot.session.get("https://keyo.me/bot/roleta.json") as roleta:
        return [
            value['text'] for _, value in json.loads(
                await roleta.content.read()
            ).items()
            if value['text'] is not None and len(value['text']) > min_chars
        ]
