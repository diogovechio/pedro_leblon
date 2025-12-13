# Internal
import logging

import asyncio
import random
import json
from asyncio import Semaphore
from typing import Optional, Dict, Any, Tuple

# External
import aiohttp

# Project
from pedro.data_structures.images import MessageImage, MessageDocument


class LLM:
    """
    Language Learning Model (LLM) client for interacting with OpenAI's API.

    This class provides methods to generate text using different OpenAI models,
    including support for web search, chat models, and completion models.
    """

    def __init__(
            self,
            api_key: str,
            default_model: str = "gpt-4.1-nano",
    ):
        """
        Initialize the LLM client.

        Args:
            api_key: OpenAI API key for authentication
            default_model: Default model to use if none is specified
        """
        self.api_key = api_key
        self.default_model = default_model

        self.session = aiohttp.ClientSession()

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        self.semaphore: Semaphore = Semaphore(2)

    async def generate_text(
            self,
            prompt: str,
            model: str = "gpt-4.1-nano",
            temperature: float = 1.0,
            image: 'MessageImage' = None,
            document: 'MessageDocument' = None,
            web_search: bool = False,
    ) -> str:
        """
        Generate text using OpenAI's API.

        Args:
            prompt: The input text prompt
            model: The model to use for generation
            temperature: Controls randomness in the response (0.0-2.0)
            image: Optional image to include with the prompt for multimodal models
            document: Optional PDF document to include with the prompt for multimodal models
            web_search: Whether to use web search capabilities

        Returns:
            The generated text response

        Note:
            Will retry up to 3 times in case of failure
        """
        for i in range(3):
            retry_sleep = int(2.0 + random.random() * 5.0)

            try:
                async with self.semaphore:
                    model = model or self.default_model
                    is_chat_model = model != "gpt-3.5-turbo-instruct"
                    file_id = None

                    if web_search:
                        endpoint, request_data = self._prepare_web_search_request(
                            prompt, model, temperature
                        )
                    elif is_chat_model:
                        # PDF upload is not yet supported, so we skip it
                        # If there's a document, we'll just include a note about it in the prompt
                        if document:
                            prompt += f"\n\n[Documento anexado: {document.file_name}. Processamento de PDF ainda não é suportado.]"

                        endpoint, request_data = self._prepare_chat_model_request(
                            prompt, model, temperature, image, file_id
                        )
                    else:
                        endpoint, request_data = self._prepare_completion_model_request(
                            prompt, model, temperature
                        )

                    response_text = await self._make_api_request(
                        endpoint=endpoint,
                        request_data=request_data,
                        is_chat_model=is_chat_model,
                        web_search=web_search
                    )
                    return response_text

            except Exception as exc:
                logging.exception(exc)
                await asyncio.sleep(retry_sleep)

        return "ué"

    @staticmethod
    def _prepare_web_search_request(
            prompt: str,
            model: str,
            temperature: float
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Prepare request data for web search.

        Args:
            prompt: The input text prompt
            model: The model to use
            temperature: Controls randomness in the response

        Returns:
            Tuple containing the endpoint URL and request data dictionary
        """
        endpoint = "https://api.openai.com/v1/responses"
        request_data = {
            "model": model,
            "input": prompt,
            "temperature": temperature,
            "tools": [{"type": "web_search_preview"}],
        }
        return endpoint, request_data

    @staticmethod
    def _prepare_chat_model_request(
            prompt: str, 
            model: str, 
            temperature: float, 
            image: Optional['MessageImage'] = None,
            file_id: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Prepare request data for chat models.

        Args:
            prompt: The input text prompt
            model: The model to use
            temperature: Controls randomness in the response
            image: Optional image to include with the prompt for multimodal models
            file_id: Optional uploaded Doc ID to include with the prompt for multimodal models

        Returns:
            Tuple containing the endpoint URL and request data dictionary
        """
        endpoint = "https://api.openai.com/v1/chat/completions"

        if image:
            # For multimodal models, include the image in the content
            content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": image.url
                    }
                }
            ]
        elif file_id:
            # For multimodal models, include the document in the content
            content = [
                {"type": "text", "text": prompt},
                {"type": "file", "file_id": file_id}
            ]
        else:
            content = prompt

        request_data = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "temperature": temperature,
        }
        return endpoint, request_data

    @staticmethod
    def _prepare_completion_model_request(
            prompt: str, 
            model: str, 
            temperature: float
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Prepare request data for completion models.

        Args:
            prompt: The input text prompt
            model: The model to use
            temperature: Controls randomness in the response

        Returns:
            Tuple containing the endpoint URL and request data dictionary

        Note:
            Completion models don't support images
        """
        endpoint = "https://api.openai.com/v1/completions"
        request_data = {
            "model": model,
            "prompt": prompt[:3000],
            "temperature": temperature,
            "max_tokens": 1024,
        }
        return endpoint, request_data

    async def _make_api_request(
            self, 
            endpoint: str, 
            request_data: Dict[str, Any], 
            is_chat_model: bool, 
            web_search: bool
    ) -> str:
        """
        Make API request and process the response.

        Args:
            endpoint: API endpoint URL
            request_data: Request data dictionary
            is_chat_model: Whether the model is a chat model
            web_search: Whether this is a web search request

        Returns:
            The processed response text
        """
        async with self.session.post(
                endpoint,
                headers=self.headers,
                json=request_data
        ) as openai_request:
            response = await openai_request.text()
            response_json = json.loads(response)

            if web_search:
                output = response_json["output"]
                if len(output) > 1:
                    response_text = output[1]["content"][0]["text"]
                else:
                    response_text = output[0]["content"][0]["text"]
            elif is_chat_model:
                response_text = response_json['choices'][0]['message']['content']
            else:
                response_text = response_json['choices'][0]['text']

            return response_text


async def upload_pdf(pdf_bytes: bytes, filename="document.pdf", api_key: str="") -> str:
    """
    Upload a PDF document to OpenAI's API.

    Args:
        pdf_bytes: The bytes of the PDF document
        filename: The name of the file
        api_key: OpenAI api key for authentication

    Returns:
        The ID of the uploaded file
    """
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    form = aiohttp.FormData()
    form.add_field("purpose", "user_data")  # Official docs recommend "user_data"
    form.add_field(
        "file",
        pdf_bytes,
        filename=filename,
        content_type="application/pdf"
    )

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/files", headers=headers, data=form) as request:
            data = await request.json()
            if request.status != 200:
                raise RuntimeError(f"Failed upload: {data}")

            return data["id"]
