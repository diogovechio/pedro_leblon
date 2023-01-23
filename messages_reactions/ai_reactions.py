import random

import openai

from constants.constants import OPENAI_BLOCK_WORDS, OPENAI_REACT_WORDS, OPENAI_PROMPTS
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.openai_utils import openai_generate_message, normalize_openai_text
from utils.roleta_utils import get_roletas_from_pavuna, arrombado_classifier


async def openai_reactions(
        bot: FakePedro,
        message: TelegramMessage,
        from_samuel: bool
) -> None:
    input_text = message.text
    username = message.from_.username if message.from_.username else message.from_.first_name

    destroy_message = True if bot.config.block_samuel and from_samuel else False

    if message.reply_to_message and message.reply_to_message.text:
        input_text += ' : ' + message.reply_to_message.text

    if openai_block_word_detected := any(
            block_word in message.text.lower() for block_word in OPENAI_BLOCK_WORDS
    ):
        if random.random() < bot.config.random_params.words_react_frequency or 'pedr' in message.text.lower():
            bot.loop.create_task(
                bot.send_message(
                    message_text=await openai_generate_message(
                        bot=bot,
                        message_data=message,
                        message_text=input_text,
                        prompt_inject=OPENAI_PROMPTS['critique'] if round(
                            random.random()) else OPENAI_PROMPTS['critique_reformule'],
                        remove_words_list=['pedro'],
                        sentences=2,
                        temperature=1.0,
                        tokens=165,
                        destroy_message=destroy_message,
                        mock_message=True
                    ),
                    chat_id=message.chat.id,
                    sleep_time=1 + (round(random.random()) * 4),
                    reply_to=message.message_id)
            )

    if not openai_block_word_detected:
        if any(
                react_word in message.text.lower() for react_word in OPENAI_REACT_WORDS
        ) and random.random() < bot.config.random_params.words_react_frequency:
            bot.loop.create_task(
                bot.send_message(
                    message_text=await openai_generate_message(
                        bot=bot,
                        message_data=message,
                        message_text=input_text,
                        prompt_inject=OPENAI_PROMPTS['fale'],
                        sentences=1,
                        tokens=150,
                        destroy_message=destroy_message,
                        mock_message=True
                    ),
                    chat_id=message.chat.id,
                    sleep_time=1 + (round(random.random()) * 5),
                    reply_to=message.message_id)
            )

        elif 'pedr' in message.text.lower()[0:5] and not "/pedro" in message.text.lower()[0:6]:
            bot.loop.create_task(
                bot.send_message(
                    message_text=await openai_generate_message(
                        bot=bot,
                        message_data=message,
                        message_text=input_text,
                        prompt_inject=OPENAI_PROMPTS[
                            'responda'] if '?' in message.text.lower() else OPENAI_PROMPTS['fale'],
                        remove_words_list=['pedro'],
                        destroy_message=destroy_message
                    ),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )

        elif from_samuel and (
            random.random() < bot.config.random_params.mock_samuel_frequency or
            any(
                react_word in message.text.lower() for react_word in OPENAI_REACT_WORDS
            )
        ):
            bot.loop.create_task(
                bot.send_message(
                    message_text=await openai_generate_message(
                        bot=bot,
                        message_data=message,
                        message_text=f"O samuel disse: {input_text}",
                        prompt_inject=OPENAI_PROMPTS['critique_negativamente'],
                        destroy_message=False
                    ),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )

        elif "/pedro" in message.text.lower()[0:6]:
            bot.loop.create_task(
                bot.send_message(
                    message_text=await openai_generate_message(
                        bot=bot,
                        message_data=message,
                        message_text=input_text,
                        prompt_inject=None,
                        destroy_message=destroy_message,
                        remove_words_list=['/pedro']
                    ),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )

        elif "/tldr" in message.text.lower()[0:5]:
            bot.loop.create_task(
                bot.send_message(
                    message_text=await openai_generate_message(
                        bot=bot,
                        message_data=message,
                        message_text=f"faça um resumo do texto a seguir: {input_text}",
                        prompt_inject=None,
                        destroy_message=destroy_message,
                        remove_words_list=None
                    ),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )
        elif "/critique" in message.text.lower()[0:9]:
            choiced_roleta = {}

            if message.reply_to_message and message.reply_to_message.text:
                arrombado = message.reply_to_message.from_.first_name
                prompt = f"{'dê uma bronca em' if round(random.random()) else 'xingue o'} {arrombado} por ter dito isso: " \
                         f"'{message.reply_to_message.text}'"
            else:
                roleta_list = await get_roletas_from_pavuna(bot, 25)
                choiced_roleta = random.choice(roleta_list)
                arrombado = arrombado_classifier(choiced_roleta)

                prompt = f"{'dê uma bronca em' if round(random.random()) else 'xingue o'} {arrombado} por ter dito isso: " \
                         f"'{choiced_roleta['text']}'"

            text = await openai_generate_message(
                        bot=bot,
                        message_data=message,
                        message_text=prompt,
                        destroy_message=destroy_message,
                        prompt_inject="O",
                        temperature=1.0,
                        sentences=2,
                        remove_words_list=['asd']
                    )

            if choiced_roleta:
                message_text = f"'{choiced_roleta['text']}'\n\n{text.upper()}"
            else:
                message_text = text.upper()

            if arrombado.lower() not in text:
                message_text = f"{arrombado}, {text}"

            bot.loop.create_task(
                bot.send_message(
                    message_text=message_text,
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )

        elif (
                len(message.text) >= 25 and True
                and message.chat.id not in bot.config.not_internal_chats
                and not bot.mocked_today
        ):
            roleta_list = (await get_roletas_from_pavuna(bot, 25))
            prompt = f"assumindo que alguém disse: '{random.choice(roleta_list)['text']}' e o {username} disse: '{message.text}', {'continue o assunto' if round(random.random()) else 'puxe outro assunto com base no que está sendo conversado'}."

            bot.loop.create_task(
                bot.send_message(
                    message_text=(
                        await normalize_openai_text(
                            ai_message=openai.Completion.create(
                                model="text-davinci-003",
                                prompt=prompt,
                                api_key=bot.config.secrets.openai_key,
                                max_tokens=bot.config.openai.max_tokens,
                                frequency_penalty=1.0,
                                presence_penalty=2.0,
                                temperature=1.0
                            ).choices[0].text,
                            sentences=2
                        )
                    ),
                    chat_id=message.chat.id,
                    sleep_time=1 + (round(random.random()) * 5),
                    reply_to=message.message_id
                )
            )

            bot.mocked_today = True
