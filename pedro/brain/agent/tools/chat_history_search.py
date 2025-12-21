from typing import Any, Dict, List, Optional
from pedro.brain.agent.tools.base import Tool
from pedro.brain.modules.chat_history import ChatHistory
from pedro.utils.text_utils import friendly_chat_log

class ChatHistorySearchTool(Tool):
    def __init__(self, history: ChatHistory, chat_id: int):
        self._history = history
        self._chat_id = chat_id

    @property
    def name(self) -> str:
        return "search_chat_history"

    @property
    def description(self) -> str:
        return (
            "Busca mensagens antigas no histórico do chat para responder perguntas sobre conversas passadas. "
            "Use isso quando o usuário perguntar 'o que fulano falou sobre X', 'qual foi a última vez que falamos sobre Y'. "
            "Se o usuário perguntar apenas 'o que estão falando?' ou 'resuma a conversa', envie a lista de queries vazia."
            "Retorna um log formatado das mensagens encontradas."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Lista de até 10 palavras-chave para buscar nas mensagens. "
                                   "Apenas palavras-chave, não frases. "
                                   "Ex: ['política', 'governo', 'eleição'] ou ['jogo', 'game', 'steam', 'console']'. "
                                   "Deixe vazio para pegar as mensagens mais recentes sem filtro.",
                    "maxItems": 10,
                },
                "days": {
                    "type": "integer",
                    "description": "Quantos dias atrás buscar (padrão: 3). Aumente se precisar de histórico mais antigo.",
                    "default": 3,
                },
                "limit": {
                    "type": "integer",
                    "description": "Número máximo de mensagens para retornar (padrão: 100).",
                    "default": 150,
                },
            },
            "required": [],
        }

    async def execute(self, queries: List[str] = None, days: int = 3, limit: int = 150) -> str:
        # Retrieve messages
        messages_dict = self._history.get_messages(self._chat_id, days_limit=days)
        
        # Flatten
        all_messages = []
        for date_str, chat_logs in messages_dict.items():
            all_messages.extend(chat_logs)

        # Filter & Deduplicate
        # We use a set of signatures (date + user + text) or just object references if stable enough, 
        # but chat logs might be recreated. Let's use the object itself if possible or a tuple.
        # Since we want to preserve order (chronological usually), we carefully collect matches.
        
        matched_messages = []
        seen_ids = set() # using (datetime, user_id, message) as unique key

        if queries:
            # Normalize queries
            normalized_queries = [q.lower().strip() for q in queries if q.strip()]
            
            for msg in all_messages:
                if not msg.message:
                    continue
                
                msg_lower = msg.message.lower()
                # Check if ANY query matches
                if any(q in msg_lower for q in normalized_queries):
                    # Dedup check
                    unique_key = (msg.datetime, msg.user_id, msg.message)
                    if unique_key not in seen_ids:
                        seen_ids.add(unique_key)
                        matched_messages.append(msg)
        else:
            # If empty queries provided (shouldn't happen given required, but safe fallback)
            matched_messages = all_messages

        # Limit (taking the most recent ones if we have too many)
        if len(matched_messages) > limit:
             matched_messages = matched_messages[-limit:]

        if not matched_messages:
            queries_str = ", ".join(queries)
            return f"Nenhuma mensagem encontrada para as buscas [{queries_str}] nos últimos {days} dias."

        # Re-sort might be needed if we were engaging in complex merging, but here we iterated chronologically (assuming all_messages was sorted)
        # all_messages comes from get_messages which sorts by date? get_messages returns dict by date, we flattened it.
        # The flattened list order depends on dict iteration order and extend. 
        # Dict insertion order is preserved in recent Python, keys were sorted in get_messages?
        # Looking at get_messages: "json_files.sort", yes. "chat_logs.sort". Yes.
        # So all_messages should be sorted.
        
        return friendly_chat_log(matched_messages)
