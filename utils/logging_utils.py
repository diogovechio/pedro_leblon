import sys
import logging
import typing as T

import aiohttp
import asyncio
import traceback
import json
from datetime import datetime

from constants.constants import SECRETS_FILE

TOKEN = json.loads(open(SECRETS_FILE).read())['secrets']['bot_token']

async def telegram_logging(text: T.Union[str, Exception], chat_id=-704277411):
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
            logging.info(f"{sys._getframe().f_code.co_name} - {resp.status}")

            await session.close()
            await asyncio.sleep(0.25)


def elapsed_time(func):
    def _elapsed_time(*args, **kwargs):
        start_time = datetime.now()
        data = func(*args, **kwargs)
        logging.info(f"{func.__name__} - elapsed time: {(datetime.now() - start_time).seconds} seconds")
        return data
    return _elapsed_time


def async_elapsed_time(func):
    async def _elapsed_time(*args, **kwargs):
        start_time = datetime.now()
        data = await func(*args, **kwargs)
        logging.info(f"{func.__name__} - elapsed time: {(datetime.now() - start_time).seconds} seconds")
        return data
    return _elapsed_time
