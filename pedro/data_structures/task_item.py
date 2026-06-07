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
    
    Optionally, a task can have a reminder datetime (reminder_at) so the bot
    will notify the user when the deadline arrives. The username and message_id
    fields allow the bot to @mention the user and reply to the original message.
    """
    id: str
    description: str
    created_by: int
    created_at: datetime
    for_chat: int
    is_group_task: bool
    reminder_at: T.Optional[datetime] = None
    recurrence: T.Optional[str] = None
    username: T.Optional[str] = None
    message_id: T.Optional[int] = None
    reminded: bool = False
