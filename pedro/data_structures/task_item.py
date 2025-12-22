# Internal
import typing as T
from datetime import datetime

# External
from pydantic.dataclasses import dataclass

# Project


@dataclass
class TaskItem:
    """
    Dataclass representing a task item.
    
    This class models task items that can be either personal (per-user)
    or group-wide. Personal tasks can only be managed by their creator,
    while group tasks can be managed by any member of the group.
    """
    id: str
    description: str
    created_by: int
    created_at: datetime
    for_chat: int
    is_group_task: bool
