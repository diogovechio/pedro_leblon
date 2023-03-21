import logging
import typing as T
import aiohttp
import asyncio
import traceback
import json

from constants.constants import SECRETS_FILE


async def telegram_logging(text: T.Union[str, Exception], chat_id=8375482):
    with open(SECRETS_FILE) as secret_file:
        if isinstance(text, Exception):
            text = "\n".join(traceback.format_exception(text))
        else:
            logging.info(text)
            text = text[:150]

        session = aiohttp.ClientSession()
        api_route = f"https://api.telegram.org/bot{json.loads(secret_file.read())['secrets']['bot_token']}"

        async with asyncio.Semaphore(1):
            async with session.post(
                    f"{api_route}/sendMessage".replace('\n', ''),
                    json={
                        "chat_id": chat_id,
                        'text': f"LOGGING:\n{text[:3800]}",
                        'disable_notification': True,
                    }
            ) as resp:
                logging.info(resp.status)

                await asyncio.sleep(0.25)
                await session.close()