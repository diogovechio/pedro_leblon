import logging
import typing as T
import aiohttp
import asyncio
import traceback
import json

from constants.constants import SECRETS_FILE

TOKEN = json.loads(open(SECRETS_FILE).read())['secrets']['bot_token']

async def telegram_logging(text: T.Union[str, Exception], chat_id=8375482):
    if isinstance(text, Exception):
        text = "\n".join(traceback.format_exception(text))
        text = "#exception\n" + text
    else:
        logging.info(text)
        text = text[:1000]

    session = aiohttp.ClientSession()
    api_route = f"https://api.telegram.org/bot{TOKEN}"

    async with asyncio.Semaphore(5):
        async with session.post(
                f"{api_route}/sendMessage".replace('\n', ''),
                json={
                    "chat_id": chat_id,
                    'text': f"#log\n{text[:3800]}",
                    'disable_notification': True,
                }
        ) as resp:
            logging.info(resp.status)

            await session.close()
            await asyncio.sleep(0.25)
