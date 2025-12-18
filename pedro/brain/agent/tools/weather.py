from typing import Any, Dict, Optional
from pedro.brain.agent.tools.base import Tool
from pedro.utils.weather_utils import get_forecast
from pedro.data_structures.bot_config import BotConfig

class WeatherTool(Tool):
    def __init__(self, config: BotConfig):
        self.config = config

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Obtém a previsão do tempo para uma localidade específica."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "A cidade ou local para verificar a previsão do tempo (ex: 'São Paulo', 'Rio de Janeiro')."
                },
                "days": {
                    "type": "integer",
                    "description": "Número de dias para a previsão (padrão é 2, máximo é 7).",
                    "default": 2
                }
            },
            "required": ["location"]
        }

    async def execute(self, location: str, days: int = 2) -> str:
        return await get_forecast(self.config, location, days)
