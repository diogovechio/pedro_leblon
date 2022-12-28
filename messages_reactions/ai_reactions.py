import random

from constants.constants import OPENAI_BLOCK_WORDS, OPENAI_REACT_WORDS, OPENAI_PROMPTS
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.openai_utils import openai_generate_message


async def openai_reactions(
        bot: FakePedro,
        message: TelegramMessage,
        from_samuel: bool
) -> None:
    input_text = message.text

    destroy_message = True if bot.config.block_samuel and from_samuel else False

    if message.reply_to_message:
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

        elif 'pedr' in message.text.lower()[0:5]:
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
