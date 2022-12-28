from datetime import datetime

from pydantic.dataclasses import dataclass

import typing as T


@dataclass
class Commemoration:
    id: str
    every_year: bool
    created_by: int
    created_at: datetime
    celebrate_at: datetime
    for_chat: int
    message: str
    anniversary: str


@dataclass
class Commemorations:
    data: T.List[Commemoration]
