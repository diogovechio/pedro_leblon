import json
import logging
import asyncio
from typing import List, Dict, Any, Optional

from pedro.brain.modules.llm import LLM
from pedro.brain.modules.telegram import Telegram
from pedro.brain.agent.tools.base import Tool
from pedro.data_structures.chat_log import ChatLog
from pedro.data_structures.images import MessageImage
from pedro.data_structures.telegram_message import Message
from pedro.utils.prompt_utils import send_telegram_log

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, llm: LLM, tools: List[Tool]):
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.tool_definitions = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters
                }
            }
            for t in tools
        ]

    async def run(
        self, 
        user_message: str, 
        history: List[ChatLog], 
        system_prompt: str,
        user_name: str = "User",
        telegram: Optional[Telegram] = None,
        original_message: Optional[Message] = None,
        image: Optional[MessageImage] = None,
    ) -> str:
        """
        Run the agent loop: Thought -> Action -> Observation.
        """
        # 1. Prepare initial messages from history
        messages = [{"role": "system", "content": system_prompt}]
        
        for log in history:
            role = "assistant" if log.username == "pedroleblonbot" else "user"
            content = log.message
            if role == "user":
                content = f"[{log.first_name}]: {content}"
            messages.append({"role": role, "content": content})

        # Add current message
        current_content = f"[{user_name}]: {user_message}"
        
        if image:
            current_content = [
                {"type": "text", "text": current_content},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image.url
                    }
                }
        ]
        
        messages.append({"role": "user", "content": current_content})

        asyncio.create_task(send_telegram_log(telegram, system_prompt))
        asyncio.create_task(send_telegram_log(telegram, "\n".join([str(message) for message in messages])))

        # 2. ReAct Loop
        max_turns = 5
        for _ in range(max_turns):
            response_data = await self.llm.chat(
                messages=messages,
                tools=self.tool_definitions if self.tool_definitions else None,
                model="gpt-5-nano" if not image else "gpt-5-mini"
            )

            if not response_data or 'choices' not in response_data:
                return "tive um erro ao pensar"

            choice = response_data['choices'][0]
            message = choice['message']
            
            # Ensure content is not None for the message history
            if message.get('content') is None:
                message['content'] = ""

            messages.append(message)

            if message.get('tool_calls'):
                # Handle tool calls
                for i, tool_call in enumerate(message['tool_calls']):
                    function_name = tool_call['function']['name']
                    function_args = json.loads(tool_call['function']['arguments'])

                    func = self.tools[function_name]

                    logger.info(f"Agent calling tool {i + 1}/{len(message['tool_calls'])}: {function_name} with {function_args}")
                    
                    if telegram and original_message:
                        asyncio.create_task(
                            send_telegram_log(
                                telegram=telegram,
                                message_text=f"Agent calling tool {i + 1}/{len(message['tool_calls'])}: <b>{function_name}</b>\nArgs: <code>{function_args}</code>",
                                message=original_message
                            )
                        )

                    tool_result = "Erro: Ferramenta não encontrada."
                    if function_name in self.tools:
                        try:
                            # Execute tool
                            result = await func.execute(**function_args)
                            tool_result = str(result)
                        except Exception as e:
                            tool_result = f"Erro na execução da ferramenta: {str(e)}"
                            logging.exception(f"Tool execution failed: {e}")

                    # Append tool result
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call['id'],
                            "content": tool_result
                        }
                    )
            else:
                # Final response (no more tool calls)
                return message['content']

        return "entrei em um loop de pensamento e cansei"
