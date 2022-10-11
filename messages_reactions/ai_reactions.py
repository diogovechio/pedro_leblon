import random

from constants.constants import openai_block_words, openai_react_words, openai_prompts
from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro
from utils.openai_utils import openai_generate_message


async def openai_reactions(
        bot: FakePedro, message:
        TelegramMessage
) -> None:
    openai_block_word_detected = False

    for block_word in openai_block_words:
        if openai_block_word_detected := block_word in message.text.lower():
            if random.random() < bot.config.random_params.words_react_frequency:
                bot.loop.create_task(
                    bot.send_message(
                        message_text=await openai_generate_message(
                            bot=bot,
                            message=message,
                            prompt_inject=openai_prompts['critique'] if round(
                                random.random()) else openai_prompts['critique_reformule'],
                            sentences=2,
                            temperature=1.0,
                            tokens=165,
                            mock_message=True
                        ),
                        chat_id=message.chat.id,
                        sleep_time=1 + (round(random.random()) * 4),
                        reply_to=message.message_id)
                )
            break

    if not openai_block_word_detected:
        for react_word in openai_react_words:
            if '?' not in message.text.lower() and react_word in message.text.lower(

            ) and random.random() < bot.config.random_params.words_react_frequency:
                bot.loop.create_task(
                    bot.send_message(
                        message_text=await openai_generate_message(
                            bot=bot,
                            message=message,
                            prompt_inject=openai_prompts['fale'],
                            mock_message=True
                        ),
                        chat_id=message.chat.id,
                        sleep_time=1 + (round(random.random()) * 5),
                        reply_to=message.message_id)
                )
                break
        if 'pedr' in message.text.lower()[0:4]:
            bot.loop.create_task(
                bot.send_message(
                    message_text=await openai_generate_message(
                            bot=bot,
                            message=message,
                            prompt_inject=openai_prompts[
                                'responda'] if '?' in message.text.lower() else openai_prompts['fale'],
                            remove_words_list=['pedro']
                        ),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )
        elif "/pedro" in message.text.lower()[0:6]:
            bot.loop.create_task(
                bot.send_message(
                    message_text=await openai_generate_message(
                            bot=bot,
                            message=message,
                            prompt_inject=None,
                            remove_words_list=['/pedro']
                        ),
                    chat_id=message.chat.id,
                    reply_to=message.message_id)
            )
        else:
            if random.random() < bot.config.random_params.random_mock_frequency:
                bot.loop.create_task(
                    bot.send_message(
                        message_text=(await openai_generate_message(
                            bot=bot,
                            message=message,
                            prompt_inject=openai_prompts['comente'],
                            sentences=1,
                            temperature=0.9,
                            tokens=150
                        )).replace('\n', ' '),
                        chat_id=message.chat.id,
                        sleep_time=1 + (round(random.random()) * 5),
                        reply_to=message.message_id)
                )
