
from pedro.brain.modules.database import Database
from pedro.brain.modules.llm import LLM

class MemoryManager:
    def __init__(self, database: Database, llm: LLM):
        self.database = database
        self.llm = llm
        self.table_name = "chat_memory"

    def get_memory_by_chat_id(self, chat_id: int) -> str:
        # retornar a lembrança no banco de dados
        results = self.database.search(self.table_name, {"chat_id": chat_id})
        if results and len(results) > 0:
            return results[0].get("memory", "")
        return ""

    async def upsert_memory_by_chat_id(self, chat_id: int, chat_history: str) -> None:
        if not chat_history or not chat_history.strip():
            return

        results = self.database.search(self.table_name, {"chat_id": chat_id})

        if not results:
            prompt = (
                f"Com base no seguinte histórico de mensagens de uma conversa:\n\n"
                f"{chat_history}\n\n"
                f"Crie um pequeno resumo da lembrança sobre o que foi conversado. "
                f"Foque nos pontos principais e no contexto da interação. "
                f"Responda diretamente com o resumo em no máximo 2 parágrafos curtos, sem introduções ou prefácios."
            )
            memory_text = await self.llm.generate_text(prompt=prompt, model="gpt-5-nano")
            memory_text = memory_text.strip()

            self.database.insert(self.table_name, {
                "chat_id": chat_id,
                "memory": memory_text
            })
        else:
            old_memory = results[0].get("memory", "")
            
            prompt_new = (
                f"Com base no seguinte histórico recente de mensagens:\n\n"
                f"{chat_history}\n\n"
                f"Crie um pequeno resumo da lembrança sobre o que foi conversado recentemente. "
                f"Foque nos pontos principais. "
                f"Responda diretamente com o resumo, sem introduções ou prefácios."
            )
            new_summary = await self.llm.generate_text(prompt=prompt_new, model="gpt-5-nano")
            new_summary = new_summary.strip()

            prompt_merge = (
                f"Consolide a memória de uma conversa do Telegram.\n\n"
                f"Memória existente anteriormente:\n"
                f"\"\"\"\n{old_memory}\n\"\"\"\n\n"
                f"Novos fatos ocorridos recentemente na conversa:\n"
                f"\"\"\"\n{new_summary}\n\"\"\"\n\n"
                f"Gere um único resumo unificado de no máximo 3 parágrafos consolidando ambas as informações. "
                f"Não repita fatos. Responda diretamente com o resumo consolidado, sem introduções ou prefácios."
            )
            merged_memory = await self.llm.generate_text(prompt=prompt_merge, model="gpt-5-nano")
            merged_memory = merged_memory.strip()

            self.database.update(
                self.table_name,
                {"memory": merged_memory},
                {"chat_id": chat_id}
            )
