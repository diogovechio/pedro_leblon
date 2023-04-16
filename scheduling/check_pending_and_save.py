from datetime import datetime
import logging
from dataclasses import asdict

from pedro_leblon import FakePedro, telegram_logging
import json
import os


def check_agenda_and_save(bot: FakePedro):
    try:
        today = bot.datetime_now

        day = today.day
        month = today.month
        year = today.year

        for entry in bot.commemorations.data:
            string_date = str(entry.celebrate_at).split(' ')[0]
            date = datetime.strptime(string_date, "%Y-%m-%d")

            if date.day == day and date.month == month and (
                    (
                            not entry.every_year and date.year == year
                    )
                    or entry.every_year
            ):
                if entry.last_celebration is None or entry.last_celebration.year != year:
                    entry.last_celebration = bot.datetime_now

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

        new_agenda_data = asdict(bot.commemorations)
        user_forecast = json.dumps(bot.config.user_last_forecast)

        for idx, _ in enumerate(new_agenda_data['data']):
            new_agenda_data['data'][idx]['created_at'] = str(new_agenda_data['data'][idx]['created_at'])
            new_agenda_data['data'][idx]['celebrate_at'] = str(new_agenda_data['data'][idx]['celebrate_at'])
            if new_agenda_data['data'][idx]['last_celebration']:
                new_agenda_data['data'][idx]['last_celebration'] = str(new_agenda_data['data'][idx]['last_celebration'])

        new_json = json.dumps(new_agenda_data['data'], indent=4)

        with open("commemorations_tmp.json", "w") as file:
            file.write(new_json)

        with open("forecast_tmp.json", "w") as file:
            file.write(user_forecast)

        if os.path.exists("commemorations.json"):
            os.remove("commemorations.json")

        if os.path.exists("forecast_users.json"):
            os.remove("forecast_users.json")

        os.rename("commemorations_tmp.json", "commemorations.json")
        os.rename("forecast_tmp.json", "forecast_users.json")
    except Exception as exc:
        bot.loop.create_task(telegram_logging(exc))
