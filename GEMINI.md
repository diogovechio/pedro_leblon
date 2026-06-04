# Pedro Leblon Bot - Guidelines & Technical Context

Welcome, Antigravity/Gemini! This document serves as the developer guidelines and context for the **Pedro Leblon Bot** project. It is automatically loaded as a workspace rule. Follow these rules and architectural descriptions strictly.

---

## 1. Core Developer Rules (MUST FOLLOW)

*   **No Hardcoding IDs or Keys**: Never hardcode chat IDs, user IDs, or API keys. Always use `secrets.json` for credentials and `bot_configs.json` for configuration values (such as allowed chat IDs, target directories, rate limits, etc.).
*   **Asynchronous-First (`asyncio`)**: The bot is entirely asynchronous. Never use blocking operations (like standard `time.sleep`, synchronous requests, or blocking I/O) in the main thread. Always use `await asyncio.sleep()` and async libraries. If synchronous code must be run, execute it in a thread pool using the loop's `run_in_executor`.
*   **Maintain Documentation & Docstrings**: Retain existing docstrings and comments when modifying code. Ensure new features are fully typed with python type hints and documented.
*   **Response Style (Persona)**: Pedro has a specific "internet user" persona:
    *   **Tone**: Sarcastic, intelligent, useful, informal.
    *   **Format**: Use all-lowercase letters for informal chat, and **no final period** at the end of responses.
    *   **Limits**: Avoid excessive emojis, formal greetings, punctuation (like multiple exclamation marks), and unnecessary questions.
*   **Error Handling**: Wrap reactions and tools in try-except blocks. Log errors using `logging.exception` to avoid silent failures. Ensure rate-limiting errors from APIs (e.g., OpenAI or Telegram) are caught gracefully.

---

## 2. Directory & Architectural Layout

```
pedro_leblon/
├── database/                    # TinyDB files and JSON chat logs
├── gifs/                        # GIFs and video files for birthday reactions
├── pedro/                       # Core Python codebase
│   ├── brain/
│   │   ├── agent/               # Autonomous ReAct agent and tools
│   │   │   ├── tools/           # Individual agent tools (Weather, Search, etc.)
│   │   │   └── core.py          # ReAct execution loop
│   │   ├── constants/           # Global word lists and constants
│   │   ├── modules/             # Key stateful components and managers
│   │   └── reactions/           # Message reactions and routing
│   │       └── main/            # Core routing and default response logic
│   ├── data_structures/         # Pydantic or basic dataclasses for type safety
│   ├── utils/                   # Shared utility modules
│   ├── __version__.py           # Bot versioning
│   └── main.py                  # Main initialization and connection class
├── .cursorrules                 # Rules for Cursor and other AI editors
├── bot_configs.json             # Main JSON configuration file
├── secrets.json                 # Secret tokens and API keys (DO NOT COMMIT)
├── run.py                       # Application runner
└── requirements.txt             # Python dependencies
```

---

## 3. Core Modules & Flow of Message Processing

### 3.1 Flow of Message Handling
1.  **Entry**: `run.py` runs `TelegramBot.run()` in [pedro/main.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/main.py).
2.  **Polling**: `TelegramBot._message_handler()` polls Telegram for new messages.
3.  **Logging**: New messages are recorded via [chat_history.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/modules/chat_history.py) and the user database is updated via [user_data_manager.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/modules/user_data_manager.py).
4.  **Routing**: The main router `messages_handler()` in [messages_handler.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/reactions/main/messages_handler.py) processes the message if the bot is unlocked.
5.  **Execution**: `messages_handler()` executes multiple reaction functions in parallel using `asyncio.gather()`. Each reaction check resolves quickly if the message does not match its triggers.

### 3.2 Core Component Managers (`pedro/brain/modules/`)
*   [telegram.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/modules/telegram.py): Wrapper for Telegram API (sends/edits/deletes messages, downloads media).
*   [llm.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/modules/llm.py): Wrapper for OpenAI model queries (supports text generation and multimodal inputs).
*   [database.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/modules/database.py): Simple wrapper around TinyDB for persistence.
*   [user_data_manager.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/modules/user_data_manager.py): Tracks user relationship metrics, sentiments, opinions, and profiles.
*   [chat_history.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/modules/chat_history.py): Saves message logs to filesystem in `database/chat_logs/` and cleans invalid JSONs.

---

## 4. How to Add a New Command or Message Reaction

1.  **Create Reaction File**: Add a new Python file in `pedro/brain/reactions/`.
2.  **Define Reaction Function**: The signature should accept the `Message` and whatever modules it needs, returning `None`. Inside the reaction, check the trigger condition (e.g., starts with a command or contains specific keywords) and exit early if it is not met.
    ```python
    # Example: pedro/brain/reactions/my_new_reaction.py
    from pedro.data_structures.telegram_message import Message
    from pedro.brain.modules.telegram import Telegram

    async def my_new_reaction_handler(message: Message, telegram: Telegram) -> None:
        if not (message.text and message.text.startswith("/mycommand")):
            return
        
        # Implement reaction logic...
        await telegram.send_message(
            message_text="comando executado com sucesso", 
            chat_id=message.chat.id
        )
    ```
3.  **Register Reaction**: Import and add your function to the `asyncio.gather()` inside `messages_handler()` in [messages_handler.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/reactions/main/messages_handler.py).

---

## 5. ReAct Agent & Writing Tools

When Pedro receives a general message or query, he triggers the ReAct Agent in [agent_common.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/reactions/main/agent_common.py). The agent can make calls to external/internal APIs using `Tools`.

### 5.1 Writing a New Agent Tool
1.  **Define the Tool**: Create a new class inheriting from `Tool` (defined in [base.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/agent/tools/base.py)).
    *   Set `name` (string).
    *   Set `description` (tells the LLM when to use it).
    *   Set `parameters` (JSON schema dictionary defining inputs).
2.  **Implement Execute**: Write the async `execute()` method.
    ```python
    # Example: pedro/brain/agent/tools/my_tool.py
    from pedro.brain.agent.tools.base import Tool

    class MyCustomTool(Tool):
        def __init__(self):
            super().__init__(
                name="my_custom_tool",
                description="Use this tool to do a specific action.",
                parameters={
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "Parameter explanation"}
                    },
                    "required": ["param1"]
                }
            )

        async def execute(self, param1: str) -> str:
            # Execute tool logic (e.g. call API or fetch data)
            return f"Resultado do custom tool com param: {param1}"
    ```
3.  **Register Tool**: Initialize and add your tool to the `tools` list in `run_agent_reaction()` inside [agent_common.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/reactions/main/agent_common.py).

---

## 6. TinyDB Usage Guidelines

*   Database instance: initialized in `TelegramBot.load_config_params()` and passed to modules like `UserDataManager` and `MemoryManager`.
*   Data Tables:
    *   `users`: Tracks sentiment levels, opinions, details.
    *   `memories`: Stores summary contexts for chats.
    *   `rate_limits`: Stores timestamps for rate-limiting calculations.
*   To retrieve or insert data, use the methods defined in `Database` ([database.py](file:///d:/OneDrive/repos/pedro_leblon/pedro/brain/modules/database.py)) instead of raw TinyDB calls if possible.

---

## 7. Testing & Verification

*   Verify syntax and code style by checking your code against Python linters or executing simple test runs.
*   Test python files locally inside the virtual environment:
    ```bash
    python run.py
    ```
*   Always inspect if logs show any parsing/exceptions during start-up.
