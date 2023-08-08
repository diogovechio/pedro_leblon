import random

from pedro_leblon import FakePedro, telegram_logging
from utils.openai_utils import list_crop, chat_log_extractor
from utils.roleta_utils import get_roletas_from_pavuna

NO_OPINION = [
    "wolo",
    "não há",
    "não tenho",
    "não encontrei",
    "mencionado",
    "citado",
    "mencionada",
    "citada",
    "não aparece",
    "nenhuma atualização",
    "não tem informações",
    "não há informações",
    "não há informação",
    "não tem informações",
    "existe informação",
    "existem informações",
    "para opinar"
]


def pedro_opinions(bot: FakePedro) -> None:
    try:
        bot.loop.create_task(
            get_opinions(bot)
        )
    except Exception as exc:
        bot.loop.create_task(telegram_logging(exc))


async def get_opinions(bot: FakePedro) -> None:
    messages = chat_log_extractor(
        chats=bot.chats_in_memory,
        message_limit=175,
        date_now=bot.datetime_now,
        max_period_days=4
    )

    users_names = [name for name in bot.user_opinions]
    user_list = [f"{key + 1} - {user.split('#')[0]}" for key, user in enumerate(users_names)]
    users = '\n'.join(user_list)

    system = {
        "role": "system",
        "content": "finja ser pedro, um observador de uma conversa. "
                   "limite-se a dizer, de maneira enumerada e respeitando os números que lhe forem passados, "
                   "a percepção de pedro para cada um com base na conversa abaixo. "
                   "caso não encontre nenhuma informação de uma pessoa na conversa, diga WOLOLOLO pra ela;"
    }

    prompt = "pedro, o que voce pensa sobre cada uma dessas pessoas?"

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

    if response[0] != "1":
        idx = response.find('1')
        response = response[idx:]

    response_parser = response.split("\n")

    for idx, response in enumerate(response_parser):
        if not any(word in response.lower() for word in NO_OPINION):
            if response[0].isdigit():
                if ":" in response:
                    text = response.split(":")[-1]
                    # name = ((response.split(":")[0]).split("-")[-1]).replace("@", ", também conhecido como ")
                    opinion = (f"{text}".lower()).strip()

                    username = users_names[idx]

                    if len(bot.user_opinions[username]) >= 5:
                        del bot.user_opinions[username][1]

                    bot.user_opinions[username].append(opinion)
