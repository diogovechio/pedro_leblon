import logging
import base64
import random
from contextlib import contextmanager
from pynvml import *
import pysftp
import asyncio
import json
import aiohttp
import re

SECRETS = json.loads(open("secrets.json").read())['secrets']

TELEGRAM_URL = f"https://api.telegram.org/bot{SECRETS['bot_token']}"


global verbose
verbose = True

nvmlInit()
h = nvmlDeviceGetHandleByIndex(0)


async def is_taking_too_long(chat_id: int, max_loops=4, timeout=13):
    messages = [f"to fazendo a imagem que vc pediu",
                "diogo deve ter me colocado em modo low vram de novo",
                "ja vou mandar",
                f"só 1 minuto"]

    global verbose
    if verbose:
        verbose = False
        for _ in range(max_loops):
            await asyncio.sleep(timeout + int(random.random() * timeout / 5))

            message = random.choice(messages)
            messages.remove(message)

            asyncio.create_task(
                send_message(
                    message_text=message,
                    chat_id=chat_id
                )
            )

            timeout *= 2


async def send_message(
    message_text: str,
    chat_id: int
) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"{TELEGRAM_URL}/sendMessage".replace('\n', ''),
                json={
                    "chat_id": chat_id,
                    'text': message_text,
                }
        ) as resp:
            print(resp.status)


@contextmanager
def sending_action(
    chat_id: int,
):
    sending = asyncio.create_task(send_action(chat_id))
    timer = asyncio.create_task(is_taking_too_long(chat_id=chat_id))
    try:
        yield
    finally:
        sending.cancel()
        timer.cancel()


async def send_action(
        chat_id: int,
        action='upload_photo',
) -> None:
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{TELEGRAM_URL}/sendChatAction".replace('\n', ''),
                data=aiohttp.FormData(
                    (
                            ("chat_id", str(chat_id)),
                            ('action', action),
                    )
                )
            ) as resp:
                print(resp)

        await asyncio.sleep(round(5 + (random.random() * 2)))


async def send_photo(image: bytes, chat_id: int, caption=None, reply_to=None, sleep_time=0,
                     max_retries=5,) -> bool:
    await asyncio.sleep(sleep_time)

    for _ in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        url=f"{TELEGRAM_URL}/sendPhoto".replace('\n', ''),
                        data=aiohttp.FormData(
                            (
                                    ("chat_id", str(chat_id)),
                                    ("photo", image),
                                    ("reply_to_message_id", str(reply_to) if reply_to else ''),
                                    ('allow_sending_without_reply', 'true'),
                                    ("caption", caption if caption else '')
                            )
                        )
                ) as resp:
                    if 200 <= resp.status < 300:
                        return True
        except Exception as exc:
            logging.exception(exc)
        await asyncio.sleep(10)

    return False

cnopts = pysftp.CnOpts()
cnopts.hostkeys = None


async def main():
    asyncio.create_task(reset_verbose_timeout())

    info = nvmlDeviceGetMemoryInfo(h)
    free_vram = round(info.free / 1024 / 1024 / 1024, 2)

    print(f"Available VRAM: {free_vram}GB")

    while True:
        try:
            with pysftp.Connection(host='159.89.85.47', username='root', password=SECRETS["ftp_pass"], cnopts=cnopts) as sftp:
                with sftp.cd("pedro_leblon/image_tasks"):
                    while True:
                        tasks = sftp.listdir()

                        if len(tasks) == 0:
                            await asyncio.sleep(10)

                        async with aiohttp.ClientSession() as session:
                            for task in tasks:
                                for _ in range(8):
                                    try:
                                        task_data = json.loads((sftp.open(task)).read())

                                        prompt = task_data["prompt"].strip()

                                        if len(prompt):
                                            first_char_digit = prompt[0].isdigit()

                                            negative_prompt = ""

                                            if "-" in prompt:
                                                split = prompt.split("-")
                                                prompt = split[0].strip()
                                                negative_prompt = split[1].strip()

                                            payload = {
                                                    "prompt": prompt[1:] if first_char_digit else prompt,
                                                    "negative_prompt": negative_prompt,
                                                }

                                            print(prompt)
                                            print(negative_prompt)

                                            ok = False

                                            with sending_action(task_data["chat_id"]):
                                                total_images = int(re.sub("\D", "", prompt.split(" ")[0])) if first_char_digit else 1
                                                if total_images > 8:
                                                    total_images = 8

                                                for i in range(total_images):
                                                    async with session.post("http://127.0.0.1:8888/v1/generation/text-to-image",
                                                                            json=payload, ssl=False) as req:

                                                        response = await req.json()

                                                        image_b64 = response[0]["base64"].encode()
                                                        image_b = base64.b64decode(image_b64)

                                                    ok = await send_photo(
                                                            image=image_b,
                                                            chat_id=task_data["chat_id"],
                                                            reply_to=task_data["message_id"] if i == 0 else None
                                                        )

                                            if ok:
                                                break
                                        
                                        else:
                                            break
                                    except Exception as exc:
                                        print(exc)
                                        await asyncio.sleep(90)

                                if ok:
                                    sftp.remove(task)

                                await asyncio.sleep(10)

        except Exception as exc:
            print(exc)
            await asyncio.sleep(10)


async def reset_verbose_timeout():
    while True:
        await asyncio.sleep(60 * 60 * 2)
        global verbose
        verbose = True


if __name__ == "__main__":
    asyncio.run(main())
