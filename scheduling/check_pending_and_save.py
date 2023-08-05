from datetime import datetime, timedelta
from dataclasses import asdict
from pathlib import Path

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

            if entry.frequency == "monthly":
                date = datetime.strptime(string_date, "%Y-%m-%d")

                if str(date.day) == "31":
                    next_month = date.replace(day=28) + timedelta(days=4)
                    date = next_month - timedelta(days=next_month.day)

                if date.day == day:
                    if entry.last_celebration is None or entry.last_celebration.month != month:
                        entry.last_celebration = bot.datetime_now

                        bot.loop.create_task(
                            bot.send_message(
                                message_text=entry.message,
                                chat_id=entry.for_chat
                            )
                        )

            else:
                date = datetime.strptime(string_date, "%Y-%m-%d")

                if date.day == day and date.month == month and (
                        (
                                not entry.frequency == "annual" and date.year == year
                        )
                        or entry.frequency == "annual"
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
        user_mood = json.dumps(bot.mood_per_user, indent=4)
        user_opinions = json.dumps(bot.user_opinions, indent=4)

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

        with open("user_mood_tmp.json", "w", encoding="utf8") as file:
            file.write(user_mood)

        with open("user_opinions_tmp.json", "w", encoding="utf8") as file:
            file.write(user_opinions)

        for entry, value in bot.chats_in_memory.items():
            dir_name = f'chat_logs/{entry.split(":")[0]}'
            file_name = entry.split(":")[-1]
            Path(dir_name).mkdir(exist_ok=True)

            chat_json = json.dumps(value, indent=4)

            tmp_dir = f"{dir_name}/{file_name}.tmp"
            json_dir = f"{dir_name}/{file_name}.json"

            with open(tmp_dir, "w", encoding="utf8") as file:
                file.write(chat_json)

            if os.path.exists(json_dir):
                os.remove(json_dir)

            os.rename(tmp_dir, json_dir)

        if os.path.exists("commemorations.json"):
            os.remove("commemorations.json")

        if os.path.exists("forecast_users.json"):
            os.remove("forecast_users.json")

        if os.path.exists("user_mood.json"):
            os.remove("user_mood.json")

        if os.path.exists("user_opinions.json"):
            os.remove("user_opinions.json")

        os.rename("commemorations_tmp.json", "commemorations.json")
        os.rename("forecast_tmp.json", "forecast_users.json")
        os.rename("user_mood_tmp.json", "user_mood.json")
        os.rename("user_opinions_tmp.json", "user_opinions.json")
    except Exception as exc:
        bot.loop.create_task(telegram_logging(exc))
