import logging
import random

from constants.constants import BOLSOFF_LIST
from pedro_leblon import FakePedro, telegram_logging
from datetime import datetime


def bosta_daily_counter(bot: FakePedro) -> None:
    try:
        bolso_expires_at = datetime.strptime('1/1/2023', "%m/%d/%Y")
        remaining = bolso_expires_at - bot.datetime_now

        if remaining.days >= 0:
            for _id in filter(lambda chat_id: chat_id < 0, bot.allowed_list):
                bot.loop.create_task(
                    bot.send_message(
                        message_text=f"faltam {remaining.days} dias {random.choice(BOLSOFF_LIST)}",
                        chat_id=_id
                    )
                )

                if remaining.days == 0:
                    bot.loop.create_task(
                        bot.send_message(
                            message_text=f"GRANDE DIA",
                            chat_id=_id,
                            sleep_time=3
                        )
                    )

                    bot.loop.create_task(
                        bot.send_video(
                            video=open(f'gifs/jair.mp4', 'rb').read(),
                            chat_id=_id
                        )
                    )

                else:
                    bot.loop.create_task(
                        bot.send_message(
                            message_text=f"grande dia! 👍" if remaining.days % 2 == 0 else "bom dia",
                            chat_id=_id,
                            sleep_time=5
                        )
                    )
    except Exception as exc:
        bot.loop.create_task(telegram_logging(exc))
