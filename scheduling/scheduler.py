import logging
import subprocess
from time import sleep

import schedule

from pedro_leblon import FakePedro

from scheduling.bolso_counter import bosta_daily_counter
from scheduling.check_pending_and_save import check_agenda_and_save
from scheduling.commemorations import fixed_commemorations
from scheduling.daily_reset import daily_routines
from scheduling.pedro_roleta import pedro_roleta
from utils.logging_utils import telegram_logging


async def scheduler(bot: FakePedro) -> None:
    # IMPORTANT: UNHANDLED EXCEPTIONS MAY BLOCK ALL OTHER SCHEDULES
    schedule.every(5).minutes.do(
        lambda: logging.info(f'Health check - {bot.datetime_now}')
    )

    schedule.every().day.at("00:05").do(
        daily_routines, bot
    )

    # schedule cannot direct call async functions, if you need to call an async function,
    # call it from the bot event loop (bot.loop.create_task), like in the 'bosta_daily_counter' function below
    schedule.every().day.at("08:30").do(
        bosta_daily_counter, bot
    )

    schedule.every().day.at("03:01").do(
        fixed_commemorations, bot
    )

    schedule.every(10).seconds.do(
        check_agenda_and_save, bot
    )

    if bot.debug_mode:
        schedule.every(10).seconds.do(
            pedro_roleta, bot
        )

    schedule.every(13).minutes.do(
        pedro_roleta, bot
    )

    schedule.every(15).minutes.do(
        _restart_proxy, bot
    )

def _restart_proxy(bot: FakePedro) -> None:
    try:
        subprocess.run(['systemctl', 'stop', 'mtprotoproxy'],
                       check=True, text=True)
        sleep(5)
        subprocess.run(['systemctl', 'start', 'mtprotoproxy'],
                       check=True, text=True)
    except Exception as exc:
        bot.loop.create_task(telegram_logging(exc))
