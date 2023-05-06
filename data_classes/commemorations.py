from datetime import datetime

from pydantic.dataclasses import dataclass

import typing as T


@dataclass
class Commemoration:
    id: str
    frequency: str
    created_by: int
    created_at: datetime
    celebrate_at: datetime
    for_chat: int
    message: str
    anniversary: str
    last_celebration: T.Optional[datetime] = None


@dataclass
class Commemorations:
    data: T.List[Commemoration]
