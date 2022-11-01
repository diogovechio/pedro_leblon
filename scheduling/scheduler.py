import logging

import schedule

from pedro_leblon import FakePedro
from scheduling.bolso_counter import bosta_counter


async def scheduler(bot: FakePedro) -> None:
    # IMPORTANT: UNHANDLED EXCEPTIONS MAY BLOCK ALL OTHER SCHEDULES
    schedule.every(15).seconds.do(
        lambda: logging.info('Scheduling health check')
    )

    # schedule do not work with async functions, if you need to call an async function,
    # call it from the bot event loop (bot.loop.create_task), like in the example bellow
    schedule.every().day.at("08:30").do(
        bosta_counter, bot
    )
