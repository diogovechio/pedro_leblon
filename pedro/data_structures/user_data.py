# Internal
import typing as T
from typing import List, Optional

# External
from pydantic.dataclasses import dataclass

@dataclass
class UserData:
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    opinions: List[str] = None
    long_term_opinion: Optional[str] = None
    tease_messages: Optional[List[str]] = None
    watched_words: List[str] = None
    relationship_sentiment: float = 0.0
    min_relationship_sentiment: float = 0.0
    last_weather_location: Optional[str] = None
    access_level: int = 1
    allow_to_delete_messages: Optional[bool] = None
    custom_behavior: Optional[str] = None

    def __post_init__(self):
        if self.opinions is None:
            self.opinions = []
        if self.watched_words is None:
            self.watched_words = []
