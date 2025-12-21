from typing import Any, Dict
from pedro.brain.agent.tools.base import Tool
from ddgs import DDGS


class WebSearchTool(Tool):
    def __init__(self):
        pass

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Realiza uma busca na web usando DuckDuckGo para obter informações atualizadas sobre qualquer tópico."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A consulta de busca para pesquisar na web (ex: 'notícias sobre inteligência artificial', 'preço do bitcoin hoje')."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Número máximo de resultados a retornar (padrão é 2, máximo recomendado é 4).",
                    "default": 2
                }
            },
            "required": ["query"]
        }

    async def execute(self, query: str, max_results: int = 5) -> str:
        """
        Execute a web search using DuckDuckGo.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            A formatted string with search results
        """
        try:
            # Limit max_results to prevent excessive data
            max_results = min(max_results, 10)
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            
            if not results:
                return f"Não encontrei resultados para: {query}"
            
            # Format results
            formatted_results = [f"Resultados da busca para '{query}':\n"]
            for i, result in enumerate(results, 1):
                title = result.get('title', 'Sem título')
                body = result.get('body', 'Sem descrição')
                url = result.get('href', '')
                
                formatted_results.append(
                    f"{i}. {title}\n"
                    f"   {body}\n"
                    f"   URL: {url}\n"
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            return f"Erro ao realizar busca: {str(e)}"
