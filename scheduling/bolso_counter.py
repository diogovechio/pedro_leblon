import random

from constants.constants import BOLSOFF_LIST
from pedro_leblon import FakePedro
from datetime import datetime, timedelta


def bosta_daily_counter(bot: FakePedro) -> None:
    bolso_expires_at = datetime.strptime('1/1/2023', "%m/%d/%Y")
    remaining = bolso_expires_at - datetime.now()

    if remaining.days >= 0:
        for _id in filter(lambda chat_id: chat_id < 0, bot.allowed_list):
            bot.loop.create_task(
                bot.send_message(
                    message_text=f"faltam {remaining.days} dias {random.choice(BOLSOFF_LIST)}",
                    chat_id=_id
                )
            )

            bot.loop.create_task(
                bot.send_message(
                    message_text=f"GRANDE DIA! 👍👍👍",
                    chat_id=_id,
                    sleep_time=3
                )
            ) if remaining.days == 0 else bot.loop.create_task(
                bot.send_message(
                    message_text=f"bom dia" if remaining.days % 2 == 0 else "grande dia! 👍",
                    chat_id=_id,
                    sleep_time=3
                )
            )
