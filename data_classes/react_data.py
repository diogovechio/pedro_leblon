from dataclasses import dataclass

from data_classes.received_message import TelegramMessage
from pedro_leblon import FakePedro


@dataclass
class ReactData:
    bot: FakePedro
    message: TelegramMessage
    from_samuel: bool
    username: str
    input_text: str
    url_detector: str
    destroy_message: bool
    mock_chat: bool
    limited_prompt: bool
