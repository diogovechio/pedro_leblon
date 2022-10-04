import logging
import random


async def greeter(
        name: str,
        match_result: float = 1.0,
        min_accepted_matches: float = 0.9
) -> str:
    logging.info(f"{name}: {match_result}")
    if match_result > min_accepted_matches:
        return random.choice([
            f'{name} fofs',
            f'oi {name}',
            f'tudo bem {name}?',
            f"oi {name} {f'lindo' if round(random.random()) else 'linda'}",
            f'gostei dessa foto {name}'
        ])
    else:
        return f'tenho {round(match_result * 100)}% de certeza que é vc {name}...'


async def message_miguxer(message: str) -> str:
    return ''.join(
        [
            letter.upper() if round(random.random()) else letter.lower()
            for letter in message
        ]
    )


async def normalize_openai_text(message: str) -> str:
    message = (', '.join(message.split('.')[:2]).replace('\n', ' ')).lower()
    while '.' in message[0] or '?' in message[0] or ',' in message[0]:
        message = message[1:]
    message = message.strip()
    while '.' in message[-1] or ',' in message[-1]:
        message = message[:-1]
    return message
