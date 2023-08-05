import random

from pedro_leblon import FakePedro, telegram_logging
from utils.openai_utils import list_crop
from utils.roleta_utils import get_roletas_from_pavuna


def pedro_opinions(bot: FakePedro) -> None:
    try:
        bot.loop.create_task(
            get_opinions(bot)
        )
    except Exception as exc:
        bot.loop.create_task(telegram_logging(exc))


async def get_opinions(bot: FakePedro) -> None:
    messages = []
    for key, chat in bot.chats_in_memory.items():
        messages = [*messages, *chat]

    messages = list_crop(messages, 100)

    messages = "\n".join(messages)
    users_names = [name for name in bot.user_opinions]
    user_list = [f"{key + 1} - {user.split('#')[0]}" for key, user in enumerate(users_names)]
    users = '\n'.join(user_list)

    system = {
        "role": "system",
        "content": "finja ser pedro, um observador de uma conversa. "
                   "limite-se a dizer, de maneira enumerada e respeitando os números que lhe forem passados, "
                   "a percepção de pedro para cada um com base na conversa abaixo."
    }

    prompt = "pedro, o que voce pensa sobre cada uma dessas pessoas? caso não encontre as mensagens da pessoa ou " \
             "não tenha informações o suficiente, " \
             "diga apenas WOLOLOLO pra ela:"

    response = await bot.openai.generate_message(
        full_text=f"{prompt}\n{users}\n\n{messages}\n\npedro:",
        prompt_inject=None,
        moderate=False,
        users_opinions=None,
        only_chatgpt=True,
        remove_words_list=None,
        temperature=0,
        replace_pre_prompt=[system]
    )

    response_parser = response.split("\n")

    for idx, response in enumerate(response_parser):
        if "wolo" not in response.lower():
            if response[0].isdigit():
                if ":" in response:
                    text = response.split(":")[-1]
                    name = (random.choice(((response.split(":")[0]).split("@")))).split("-")[-1]
                    opinion = (f"{name}{text}.".lower()).strip()

                    username = users_names[idx]

                    if len(bot.user_opinions[username]) > 5:
                        del bot.user_opinions[username][0]

                    bot.user_opinions[username].append(opinion)
