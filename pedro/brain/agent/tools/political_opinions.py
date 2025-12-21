from typing import Any, Dict
from pedro.brain.agent.tools.base import Tool
from pedro.brain.constants.constants import POLITICAL_OPINIONS

class PoliticalOpinionsTool(Tool):
    @property
    def name(self) -> str:
        return "consult_political_opinions"

    @property
    def description(self) -> str:
        return "Consulta as opiniões políticas do Pedro. Use esta ferramenta quando se falar sobre política ou perguntarem o que o Pedro acha de determinado político."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self) -> str:
        return "\n".join(POLITICAL_OPINIONS)
