import random

from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro


async def model_selector(
        bot: FakePedro,
        message: TelegramMessage,
        mock_message=False,
        random_model=False
) -> str:
    if random_model:
        return random.choice(["ada", "curie", "text-davinci-002", "babbage"])
    if message.from_.username in bot.config.openai.only_ada_users and not mock_message:
        return "ada"
    elif bot.openai_used < bot.config.openai.davinci_daily_limit:
        return "text-davinci-002"
    elif bot.openai_used < bot.config.openai.curie_daily_limit:
        return "curie"
    else:
        return "ada"
