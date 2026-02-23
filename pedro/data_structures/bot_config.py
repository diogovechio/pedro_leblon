# Internal
import typing as T

from pydantic import Field
# External
from pydantic.dataclasses import dataclass

# Project


@dataclass
class Chats:
    name: str
    id: int


@dataclass
class BotSecret:
    bot_token: str
    openai_key: str
    deepseek_key: str = ""
    open_weather: str = ""


@dataclass
class BotConfig:
    allowed_ids: list[Chats]
    secrets: BotSecret
    not_internal_chats: T.List[int] = Field(default_factory=list)
