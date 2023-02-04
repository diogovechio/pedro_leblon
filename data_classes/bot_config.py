from pydantic import Field
from pydantic.dataclasses import dataclass
import typing as T


@dataclass
class FaceClassifier:
    face_tolerance: float
    face_min_accepted_matches: float
    box_min_size: int


@dataclass
class RandomParams:
    random_mock_frequency: float
    words_react_frequency: float
    mock_drunk_decaptor_frequency: float
    mock_samuel_frequency: float


@dataclass
class RSSFeed:
    news: str
    games: str


@dataclass
class UserID:
    name: str
    id: int


@dataclass
class MockMessage:
    last_mock_hour: int = 0
    messages: T.List[str] = Field(default_factory=list)


@dataclass
class OpenAI:
    davinci_daily_limit: int
    curie_daily_limit: int
    max_sentences: int
    max_tokens: int
    ada_only_users: T.List[str]
    force_model: T.Optional[str] = None
    dall_e_daily_limit = 30

@dataclass
class BotSecret:
    bot_token: str
    openai_key: str
    alternate_bot_token: str

@dataclass
class BotConfig:
    secrets: BotSecret
    openai: OpenAI
    ask_photos: bool
    telegram_api_semaphore: int
    face_classifier: FaceClassifier
    random_params: RandomParams
    rss_feed: RSSFeed
    allowed_ids: T.List[UserID]
    mock_messages: T.Dict[str, MockMessage]
    block_samuel: bool
    not_internal_chats: T.List[int] = Field(default_factory=list)
    auto_leave_chats: T.List[int] = Field(default_factory=list)
