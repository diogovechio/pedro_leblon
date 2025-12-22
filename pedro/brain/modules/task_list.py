# Internal
import logging
from dataclasses import asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

# Project
from pedro.data_structures.task_item import TaskItem
from pedro.brain.modules.database import Database


class TaskListManager:
    """
    Manager class for handling task list operations.
    Provides methods to create, read, and delete task items.
    Supports both personal tasks (per-user) and group tasks.
    """

    def __init__(self, db_path: str = "database/pedro_database.json"):
        """
        Initialize the TaskListManager with a database connection.

        Args:
            db_path: Path to the database file
        """
        self.db = Database(db_path)
        self.table_name = "task_list"

    def add_task_item(self, 
                      description: str,
                      created_by: int, 
                      for_chat: int,
                      is_group_task: bool) -> TaskItem:
        """
        Add a new task item to the database.

        Args:
            description: Description of the task
            created_by: ID of the user who created the task
            for_chat: ID of the chat where the task belongs
            is_group_task: Whether this is a group task or personal task

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
            is_group_task=is_group_task
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

    def _dict_to_task(self, data: Dict[str, Any]) -> TaskItem:
        """
        Convert a dictionary to a TaskItem object.

        Args:
            data: Dictionary with task data

        Returns:
            TaskItem object
        """
        return TaskItem(
            id=data["id"],
            description=data["description"],
            created_by=data["created_by"],
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            for_chat=data["for_chat"],
            is_group_task=data["is_group_task"]
        )
