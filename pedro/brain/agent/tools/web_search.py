import logging
from typing import Any, Dict
import aiohttp
import asyncio
from pedro.brain.agent.tools.base import Tool
from pedro.utils.url_utils import html_paragraph_extractor
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
                    "description": "Número máximo de resultados a retornar (padrão é 8, máximo recomendado é 24).",
                    "default": 8
                }
            },
            "required": ["query"]
        }

    async def execute(self, query: str, max_results: int = 8) -> str:
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
            max_results = min(max_results, 24)
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            
            if not results:
                return f"Não encontrei resultados para: {query}"

            # Fetch the full text for each URL concurrently
            async def fetch_full_text(session: aiohttp.ClientSession, url: str) -> str:
                if not url:
                    return ""
                try:
                    headers = {"User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) "
                                             "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}
                    timeout = aiohttp.ClientTimeout(total=4)
                    async with session.get(url, headers=headers, timeout=timeout) as site:
                        html_content = await site.text()
                        return await html_paragraph_extractor(html_content, char_limit=1500)
                except Exception as exc:
                    logging.error(f"Exception encountered: {exc}")
                    return ""

            async with aiohttp.ClientSession() as session:
                tasks = [fetch_full_text(session, r.get('href', '')) for r in results]
                full_texts = await asyncio.gather(*tasks)
            
            # Format results
            formatted_results = [f"Resultados da busca para '{query}':\n"]
            for i, (result, full_text) in enumerate(zip(results, full_texts), 1):
                # Add full_text key to result dict as requested
                result['full_text'] = full_text
                
                title = result.get('title', 'Sem título')
                body = result.get('body', 'Sem descrição')
                url = result.get('href', '')
                
                res_str = (
                    f"{i}. {title}\n"
                    f"   {body}\n"
                    f"   URL: {url}\n"
                )
                if full_text:
                    res_str += f"   Texto completo: {full_text}\n"
                formatted_results.append(res_str)
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            return f"Erro ao realizar busca: {str(e)}"

