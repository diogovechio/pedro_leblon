import logging
from dataclasses import asdict

from pedro_leblon import FakePedro
import json
import os


def check_and_save(bot: FakePedro):
    try:
        new_data = asdict(bot.commemorations)

        for idx, _ in enumerate(new_data['data']):
            new_data['data'][idx]['created_at'] = str(new_data['data'][idx]['created_at'])
            new_data['data'][idx]['celebrate_at'] = str(new_data['data'][idx]['celebrate_at'])

        new_json = json.dumps(new_data['data'], indent=4)

        with open("commemorations_tmp.json", "w") as file:
            file.write(new_json)

        if os.path.exists("commemorations.json"):
            os.remove("commemorations.json")

        os.rename("commemorations_tmp.json", "commemorations.json")
    except Exception as exc:
        logging.exception(exc)
