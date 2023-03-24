from pydantic import Field
from pydantic.dataclasses import dataclass
import typing as T


@dataclass
class Photo:
    file_id: T.Optional[str] = None
    file_unique_id: T.Optional[str] = None
    file_size: T.Optional[int] = None
    width: T.Optional[int] = None
    height: T.Optional[int] = None


@dataclass
class Chat:
    id: int
    first_name: T.Optional[str] = None
    last_name: T.Optional[str] = None
    username: T.Optional[str] = None
    type: T.Optional[str] = None
    title: T.Optional[str] = None


@dataclass
class From:
    id: int
    is_bot: bool = False
    is_premium: bool = False
    first_name: T.Optional[str] = None
    last_name: T.Optional[str] = None
    username: T.Optional[str] = None
    language_code: str = ''


@dataclass
class ReplyToMessage:
    message_id: T.Optional[int] = None
    from_: T.Optional[From] = None
    chat: T.Optional[Chat] = None
    date: T.Optional[int] = None
    text: T.Optional[str] = None


@dataclass
class TelegramMessage:
    from_: From
    message_id: T.Optional[int] = None
    chat: T.Optional[Chat] = None
    date: T.Optional[int] = None
    text: T.Optional[str] = None
    reply_to_message: T.Optional[ReplyToMessage] = None
    photo: T.Optional[T.List[Photo]] = None
    edit_date: T.Optional[int] = None
    caption: T.Optional[str] = None


@dataclass
class MessageReceived:
    update_id: T.Optional[int] = None
    message: T.Optional[TelegramMessage] = None
    edited_message: T.Optional[TelegramMessage] = None


@dataclass
class MessagesResults:
    ok: bool = False
    result: T.List[MessageReceived] = Field(default_factory=list)
