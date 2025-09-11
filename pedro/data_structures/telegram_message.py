# Internal
import typing as T

# External
from pydantic.dataclasses import dataclass
from pydantic import Field

# Project


@dataclass
class Photo:
    file_id: T.Optional[str] = None
    file_unique_id: T.Optional[str] = None
    file_size: T.Optional[int] = None
    width: T.Optional[int] = None
    height: T.Optional[int] = None


@dataclass
class Document:
    file_id: T.Optional[str] = None
    file_unique_id: T.Optional[str] = None
    file_size: T.Optional[int] = None
    file_name: T.Optional[str] = None
    mime_type: T.Optional[str] = None


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
class PollOption:
    text: str
    voter_count: int


@dataclass
class Poll:
    id: str
    question: str
    options: T.List[PollOption]
    total_voter_count: int
    is_closed: bool
    is_anonymous: bool
    type: str
    allows_multiple_answers: bool


@dataclass
class ReplyToMessage:
    message_id: T.Optional[int] = None
    from_: T.Optional[From] = None
    chat: T.Optional[Chat] = None
    date: T.Optional[int] = None
    text: T.Optional[str] = None
    caption: T.Optional[str] = None
    photo: T.Optional[T.List[Photo]] = None
    document: T.Optional[Document] = None
    poll: T.Optional[Poll] = None


@dataclass
class Message:
    from_: From
    message_id: T.Optional[int] = None
    chat: T.Optional[Chat] = None
    date: T.Optional[int] = None
    text: T.Optional[str] = None
    reply_to_message: T.Optional[ReplyToMessage] = None
    photo: T.Optional[T.List[Photo]] = None
    document: T.Optional[Document] = None
    edit_date: T.Optional[int] = None
    caption: T.Optional[str] = None
    poll: T.Optional[Poll] = None


@dataclass
class MessageReceived:
    update_id: T.Optional[int] = None
    message: T.Optional[Message] = None
    edited_message: T.Optional[Message] = None


@dataclass
class MessagesResults:
    ok: bool = False
    result: T.List[MessageReceived] = Field(default_factory=list)
