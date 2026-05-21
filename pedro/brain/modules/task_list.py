# Internal
import logging
import asyncio
from dataclasses import asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

# Project
from pedro.data_structures.task_item import TaskItem
from pedro.brain.modules.database import Database
from pedro.brain.modules.telegram import Telegram


class TaskListManager:
    """
    Manager class for handling task list operations.
    Provides methods to create, read, and delete task items.
    Supports both personal tasks (per-user) and group tasks.
    Also supports optional reminders that notify users at a specified time.
    """

    def __init__(self, telegram: Telegram, db_path: str = "database/pedro_database.json"):
        """
        Initialize the TaskListManager with a database connection.

        Args:
            telegram: Telegram instance used to send reminder messages
            db_path: Path to the database file
        """
        self.db = Database(db_path)
        self.table_name = "task_list"
        self.telegram = telegram

        asyncio.create_task(self.check_reminders())

    def add_task_item(self, 
                      description: str,
                      created_by: int, 
                      for_chat: int,
                      is_group_task: bool,
                      reminder_at: Optional[datetime] = None,
                      username: Optional[str] = None,
                      message_id: Optional[int] = None) -> TaskItem:
        """
        Add a new task item to the database.

        Args:
            description: Description of the task
            created_by: ID of the user who created the task
            for_chat: ID of the chat where the task belongs
            is_group_task: Whether this is a group task or personal task
            reminder_at: Optional datetime for when the bot should remind the user (GMT-3)
            username: Optional Telegram username (without @) for mentioning in reminders
            message_id: Optional message ID of the original request to reply to

        Returns:
            The created TaskItem object
        """
        # Get all existing task items to find the highest ID
        existing_items = self.get_all_task_items()

        # Find the highest existing ID
        highest_id = -1
        for item in existing_items:
            try:
                item_id = int(item.id)
                if item_id > highest_id:
                    highest_id = item_id
            except ValueError:
                # Skip items with non-integer IDs
                pass

        # Generate a new sequential ID
        new_id = str(highest_id + 1)

        task_item = TaskItem(
            id=new_id,
            description=description,
            created_by=created_by,
            created_at=datetime.now(),
            for_chat=for_chat,
            is_group_task=is_group_task,
            reminder_at=reminder_at,
            username=username,
            message_id=message_id,
            reminded=False
        )

        self.db.insert(self.table_name, asdict(task_item))
        return task_item

    def get_all_task_items(self) -> List[TaskItem]:
        """
        Get all task items from the database.

        Returns:
            List of TaskItem objects
        """
        items = self.db.get_all(self.table_name)
        return [self._dict_to_task(item) for item in items]

    def get_task_items_for_user(self, user_id: int) -> List[TaskItem]:
        """
        Get all personal tasks for a specific user across all chats.

        Args:
            user_id: ID of the user

        Returns:
            List of TaskItem objects for the specified user
        """
        items = self.db.search(self.table_name, {
            "created_by": user_id,
            "is_group_task": False
        })
        return [self._dict_to_task(item) for item in items]

    def get_task_items_for_group(self, chat_id: int) -> List[TaskItem]:
        """
        Get all group tasks for a specific chat.

        Args:
            chat_id: ID of the chat

        Returns:
            List of TaskItem objects for the specified chat
        """
        items = self.db.search(self.table_name, {
            "for_chat": chat_id,
            "is_group_task": True
        })
        return [self._dict_to_task(item) for item in items]

    def get_task_item_by_id(self, item_id: str) -> Optional[TaskItem]:
        """
        Get a task item by its ID.

        Args:
            item_id: ID of the task item

        Returns:
            TaskItem object if found, None otherwise
        """
        items = self.db.search(self.table_name, {"id": item_id})
        return self._dict_to_task(items[0]) if items else None

    def delete_task_item(self, item_id: str) -> bool:
        """
        Delete a task item.

        Args:
            item_id: ID of the task item to delete

        Returns:
            True if the deletion was successful, False otherwise
        """
        result = self.db.remove(self.table_name, {"id": item_id})
        return len(result) > 0

    def get_pending_reminders(self) -> List[TaskItem]:
        """
        Get all task items that have a reminder due (reminder_at <= now GMT-3)
        and have not yet been reminded.

        Returns:
            List of TaskItem objects with pending reminders
        """
        gmt3_timezone = timezone(timedelta(hours=-3))
        now = datetime.now(gmt3_timezone)

        all_items = self.get_all_task_items()
        pending = []

        for item in all_items:
            if item.reminder_at and not item.reminded:
                reminder_dt = item.reminder_at
                # Make reminder_at timezone-aware if it isn't
                if reminder_dt.tzinfo is None:
                    reminder_dt = reminder_dt.replace(tzinfo=gmt3_timezone)
                if reminder_dt <= now:
                    pending.append(item)

        return pending

    def mark_as_reminded(self, item_id: str) -> bool:
        """
        Mark a task item as reminded by updating its 'reminded' field.

        Args:
            item_id: ID of the task item

        Returns:
            True if the update was successful, False otherwise
        """
        result = self.db.update(self.table_name, {"reminded": True}, {"id": item_id})
        return len(result) > 0

    async def check_reminders(self) -> None:
        """
        Continuously checks for task reminders that need to be triggered.

        This method runs in an infinite loop checking every 30 seconds for tasks
        with a reminder_at that has passed and reminded == False. When a reminder
        is due, it sends a message via Telegram (optionally replying to the original
        message and mentioning the user) and marks the task as reminded.

        Returns:
            None. Method runs indefinitely until the program is terminated.
        """
        while True:
            try:
                pending = self.get_pending_reminders()

                for task in pending:
                    try:
                        # Build reminder message
                        if task.username:
                            reminder_text = f"⏰ @{task.username}, lembrete: {task.description}"
                        else:
                            reminder_text = f"⏰ Lembrete: {task.description}"

                        # Send reminder message
                        if self.telegram:
                            await self.telegram.send_message(
                                message_text=reminder_text,
                                chat_id=task.for_chat,
                                reply_to=task.message_id,
                                parse_mode=""
                            )

                        # Mark as reminded
                        self.mark_as_reminded(task.id)

                        logging.info(f"Reminder sent for task {task.id}: {task.description}")

                    except Exception as exc:
                        logging.exception(f"Error sending reminder for task {task.id}: {exc}")

            except Exception as exc:
                logging.exception(f"Error in check_reminders: {exc}")

            await asyncio.sleep(30)

    def _dict_to_task(self, data: Dict[str, Any]) -> TaskItem:
        """
        Convert a dictionary to a TaskItem object.

        Args:
            data: Dictionary with task data

        Returns:
            TaskItem object
        """
        # Parse reminder_at with backward compatibility
        reminder_at = data.get("reminder_at")
        if reminder_at and isinstance(reminder_at, str):
            reminder_at = datetime.fromisoformat(reminder_at)

        return TaskItem(
            id=data["id"],
            description=data["description"],
            created_by=data["created_by"],
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            for_chat=data["for_chat"],
            is_group_task=data["is_group_task"],
            reminder_at=reminder_at,
            username=data.get("username"),
            message_id=data.get("message_id"),
            reminded=data.get("reminded", False)
        )
