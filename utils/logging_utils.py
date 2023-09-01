import sys
import logging
import typing as T
from asyncio import Semaphore
from random import random

import aiohttp
import asyncio
import traceback
import json
from datetime import datetime

from constants.constants import SECRETS_FILE

TOKEN = json.loads(open(SECRETS_FILE).read())['secrets']['bot_token']
SEMAPHORE = Semaphore(1)


async def telegram_logging(text: T.Union[str, Exception], chat_id=-704277411):
    if isinstance(text, Exception):
        text = "\n".join(traceback.format_exception(text))
        text = "#exception\n" + text
    else:
        logging.info(text)
        text = text[:3800]

    session = aiohttp.ClientSession()
    api_route = f"https://api.telegram.org/bot{TOKEN}"

    async with SEMAPHORE:
        await session.post(
                f"{api_route}/sendMessage".replace('\n', ''),
                json={
                    "chat_id": chat_id,
                    'text': f"#log\n{text[:3800]}",
                    'disable_notification': True,
                }
        )
        await session.close()
        await asyncio.sleep(0.25)


def elapsed_time(func):
    def _elapsed_time(*args, **kwargs):
        start_time = datetime.now()
        data = func(*args, **kwargs)
        elapsed = datetime.now() - start_time
        logging.info(f"{func.__name__} - Elapsed time: {round(elapsed.total_seconds(), 3)} seconds")
        return data
    return _elapsed_time


def async_elapsed_time(func):
    async def _elapsed_time(*args, **kwargs):
        start_time = datetime.now()
        data = await func(*args, **kwargs)
        elapsed = datetime.now() - start_time
        logging.info(f"{func.__name__} - Elapsed time: {round(elapsed.total_seconds(), 3)} seconds")
        return data
    return _elapsed_time
