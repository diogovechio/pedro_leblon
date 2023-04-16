import json
import typing as T
from asyncio import get_running_loop, wait_for

from constants.constants import WEATHER_PROMPT

from geopy.geocoders import Nominatim

from pedro_leblon import FakePedro
from utils.logging_utils import telegram_logging


async def weather_prompt(message: str) -> str:
    return f"dado a seguinte mensagem:\n\n'{message}'\n\n{WEATHER_PROMPT}"

async def get_forecast(bot: FakePedro, place: T.Optional[str], days: T.Optional[int]) -> str:
    if not place:
        place = "russia"
    if not days:
        days = 2
    elif isinstance(days, int) and days > 7:
        days = 7

    try:
        forecast = [f"previsão do tempo em {place}:"]

        local = await wait_for(
            get_lat_lon(place),
            timeout=300
        )

        lat, lon = local

        app_id = bot.config.secrets.open_weather

        async with bot.session.get(f"https://api.openweathermap.org/data/3.0/onecall?"
                                   f"cnt={days}&units=imperial&lat={lat}&lon={lon}&lang=pt&appid={app_id}") as req:
            resp = json.loads(await req.text())

            if 'daily' in resp and isinstance(resp['daily'], list):
                for i, x in enumerate(resp['daily'][:int(days)]):
                    if i == 0:
                        day = f"Hoje: "
                    elif i == 1:
                        day = f"Amanhã: "
                    else:
                        day = f"{i + 1} dias depois de amanhã: "

                    forecast.append(
                        f"{day}predominantemente {x['weather'][0]['description']}, temperatura em {f_to_c(x['temp']['day'])}c°, "
                        f"máxima de {f_to_c(x['temp']['max'])} e "
                        f"mínima de {f_to_c(x['temp']['min'])}c°, "
                        f"sensação térmica de {f_to_c(x['feels_like']['day'])}c°")

            return "\n".join(forecast)

    except Exception as exc:
        get_running_loop().create_task(telegram_logging(exc))

    return "muito frio no japão"


async def get_lat_lon(place: str) -> tuple:
    geolocator = Nominatim(
        user_agent="Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148")
    location = geolocator.geocode(place)

    return location.latitude, location.longitude


def f_to_c(value: int) -> int:
    return int((value - 32) * 5 / 9)
