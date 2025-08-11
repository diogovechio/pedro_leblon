# Internal
from typing import Any, Dict, List
import os
import shutil
import glob
from datetime import datetime

# External
from tinydb import TinyDB, Query


class Database:
    def __init__(self, db_path: str = "pedro_database.json"):
        self.db_path = db_path
        self.db = TinyDB(db_path, indent=4, encoding='utf-8')
        self.query = Query()
        self.default_db_name = "pedro_database.json"

    def _create_backup(self):
        if self.default_db_name in self.db_path and os.path.exists(self.db_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{os.path.splitext(self.db_path)[0]}_{timestamp}_bak.json"

            shutil.copy2(self.db_path, backup_path)

            backup_pattern = f"{os.path.splitext(self.db_path)[0]}_*_bak.json"
            backup_files = sorted(glob.glob(backup_pattern), key=os.path.getmtime, reverse=True)

            if len(backup_files) > 5:
                for old_backup in backup_files[5:]:
                    os.remove(old_backup)

    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        def _normalize_data(data: Dict[str, Any]) -> Dict[str, Any]:
            normalized_data = {}

            for key, value in data.items():
                if isinstance(value, datetime):
                    normalized_data[key] = value.isoformat()
                elif isinstance(value, dict):
                    normalized_data[key] = _normalize_data(value)
                elif isinstance(value, list):
                    normalized_data[key] = [
                        item.isoformat() if isinstance(item, datetime)
                        else _normalize_data(item) if isinstance(item, dict)
                        else item
                        for item in value
                    ]
                else:
                    normalized_data[key] = value

            return normalized_data

        data = _normalize_data(data)

        table = self.db.table(table_name)
        result = table.insert(data)
        self._create_backup()
        return result

    def get_all(self, table_name: str) -> List[Dict[str, Any]]:
        table = self.db.table(table_name)
        return table.all()

    def search(self, table_name: str, condition: Dict[str, Any]) -> List[Dict[str, Any]]:
        table = self.db.table(table_name)
        query = self.query

        query_obj = None
        for key, value in condition.items():
            if query_obj is None:
                query_obj = (query[key] == value)
            else:
                query_obj &= (query[key] == value)

        return table.search(query_obj) if query_obj else []

    def update(self, table_name: str, data: Dict[str, Any], condition: Dict[str, Any]) -> List[int]:
        table = self.db.table(table_name)
        query = self.query

        query_obj = None
        for key, value in condition.items():
            if query_obj is None:
                query_obj = (query[key] == value)
            else:
                query_obj &= (query[key] == value)

        result = table.update(data, query_obj) if query_obj else []
        self._create_backup()
        return result

    def remove(self, table_name: str, condition: Dict[str, Any]) -> List[int]:
        table = self.db.table(table_name)
        query = self.query

        # Build query dynamically based on condition
        query_obj = None
        for key, value in condition.items():
            if query_obj is None:
                query_obj = (query[key] == value)
            else:
                query_obj &= (query[key] == value)

        return table.remove(query_obj) if query_obj else []

    def close(self) -> None:
        self.db.close()
