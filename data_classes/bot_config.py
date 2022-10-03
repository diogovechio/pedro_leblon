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


@dataclass
class RSSFeed:
    url: str


@dataclass
class UserID:
    name: str
    id: int


@dataclass
class MockMessage:
    lastmock: int = 0
    messages: T.List[str] = Field(default_factory=list)


@dataclass
class BotConfig:
    token: str
    face_classifier: FaceClassifier
    random_params: RandomParams
    rss_feed: RSSFeed
    allowed_ids: T.List[UserID]
    mock_messages: T.Dict[str, MockMessage]
