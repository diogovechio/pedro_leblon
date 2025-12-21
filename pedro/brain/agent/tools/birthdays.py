from typing import Any, Dict, List
from pedro.brain.agent.tools.base import Tool
from pedro.brain.modules.database import Database
from pedro.data_structures.agenda import Agenda
from datetime import datetime

class BirthdaySearchTool(Tool):
    def __init__(self, chat_id: int, db_path: str = "database/pedro_database.json"):
        self.chat_id = chat_id
        self.db = Database(db_path)
        self.table_name = "agenda"

    @property
    def name(self) -> str:
        return "search_birthdays"

    @property
    def description(self) -> str:
        return (
            "Busca aniversários agendados neste chat. "
            "Use esta ferramenta para responder perguntas como 'quando é o aniversário de fulano?'. "
            "Se o usuário quiser AGENDAR um novo aniversário, instrua-o a usar o comando /aniversario."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self) -> str:
        items = self.db.search(self.table_name, {"for_chat": self.chat_id})
        
        # Filter for birthdays (items with non-empty 'anniversary' field)
        birthdays = [item for item in items if item.get("anniversary")]

        if not birthdays:
            return "Não há aniversários registrados neste grupo."

        result = "Aniversários encontrados:\n"
        for b in birthdays:
            date_str = b.get('celebrate_at')
            try:
                # Handle both string and datetime objects just in case
                if isinstance(date_str, str):
                    dt = datetime.fromisoformat(date_str)
                else:
                    dt = date_str
                # Format to show Day/Month
                formatted_date = dt.strftime("%d/%m")
            except Exception:
                formatted_date = str(date_str)

            result += f"- {b.get('anniversary')}: {formatted_date}\n"

        return result
