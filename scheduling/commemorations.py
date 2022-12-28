from dataclasses import asdict
from datetime import datetime
import logging

from pedro_leblon import FakePedro


def commemorations(bot: FakePedro) -> None:
    try:
        today = bot.datetime_now

        day = today.day
        month = today.month
        year = today.year

        if day == 25 and month == 12:
            for _id in filter(lambda chat_id: chat_id < 0, bot.allowed_list):
                bot.loop.create_task(
                    bot.send_message(
                        message_text=f"feliz natal",
                        chat_id=_id
                    )
                )

                bot.loop.create_task(
                    bot.send_video(
                        video=open(f'gifs/feliznatal.mp4', 'rb').read(),
                        chat_id=_id
                    )
                )

        if day == 1 and month == 1:
            for _id in filter(lambda chat_id: chat_id < 0, bot.allowed_list):
                bot.loop.create_task(
                    bot.send_message(
                        message_text=f"FELIZ ANO NOVO",
                        chat_id=_id
                    )
                )

                bot.loop.create_task(
                    bot.send_video(
                        video=open(f'gifs/anonovo.mp4', 'rb').read(),
                        chat_id=_id
                    )
                )

        for entry in bot.commemorations.data:
            string_date = str(entry.celebrate_at).split(' ')[0]
            date = datetime.strptime(string_date, "%Y-%m-%d")

            if date.day == day and date.month == month and (
                    (
                        not entry.every_year and date.year == year
                    )
                    or entry.every_year
            ):
                if entry.anniversary:
                    bot.loop.create_task(
                        bot.send_message(
                            message_text=f"feliz aniversário {entry.anniversary}\n{entry.message}".upper(),
                            chat_id=entry.for_chat
                        )
                    )

                    bot.loop.create_task(
                        bot.send_video(
                            video=open(f'gifs/birthday0.mp4', 'rb').read(),
                            chat_id=entry.for_chat
                        )
                    )

                else:
                    bot.loop.create_task(
                        bot.send_message(
                            message_text=entry.message,
                            chat_id=entry.for_chat
                        )
                    )

    except Exception as exc:
        logging.exception(exc)
