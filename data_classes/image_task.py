from dataclasses import dataclass


@dataclass
class ImageTask:
    prompt: str
    chat_id: int
    message_id: int
    args: list
