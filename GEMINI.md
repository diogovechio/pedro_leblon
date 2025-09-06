# Pedro Leblon Bot - Technical Documentation

## Project Overview

Pedro Leblon is a sophisticated Telegram bot built with Python. It uses a modular architecture and leverages OpenAI's language models to provide a wide range of functionalities. The bot can engage in conversations, react to messages, manage a schedule, check the weather, and much more. It's designed to be extensible and configurable.

## Architecture

The project is structured in a modular way, with a clear separation of concerns.

-   **`pedro/main.py`**: The main entry point of the application. It initializes all the modules, loads the configuration, and starts the message handling loop.
-   **`pedro/brain/modules/`**: This directory contains the core logic of the bot, with each file representing a specific functionality (e.g., `telegram.py`, `llm.py`, `database.py`).
-   **`pedro/brain/reactions/`**: This directory contains the logic for how the bot reacts to different types of messages and commands. Each file defines a specific set of reactions.
-   **`pedro/data_structures/`**: This directory contains the data classes used throughout the project, ensuring a consistent data model.
-   **`pedro/utils/`**: This directory contains utility functions that are used across different modules.
-   **`database/`**: This directory stores the TinyDB database files and chat logs.

## Modules (`pedro/brain/modules/`)

-   **`telegram.py`**: Handles all communication with the Telegram Bot API. It provides methods for sending and receiving messages, media, and other actions. It also includes a message polling mechanism.
-   **`llm.py`**: A client for interacting with OpenAI's API. It supports text generation with different models, including multimodal input with images and documents, and web search capabilities.
-   **`database.py`**: A wrapper around the TinyDB library for data persistence. It provides a simple interface for inserting, retrieving, updating, and deleting data.
-   **`chat_history.py`**: Manages the chat logs. It records all messages in a structured way, organized by chat and date. It can also process images and documents in messages.
-   **`user_data_manager.py`**: Manages user data, including their opinions, relationship sentiment, and other preferences. It uses the LLM to analyze message tone and form opinions about users.
-   **`agenda.py`**: Manages scheduled events and reminders. It allows users to create, list, and delete agenda items with different frequencies (annual, monthly, once).
-   **`scheduler.py`**: A task scheduler for periodic jobs, such as processing historical messages, creating database backups, and resetting daily flags.
-   **`datetime_manager.py`**: A utility for handling dates and times, with support for timezones.
-   **`feedback.py`**: Provides feedback to the user during long-running operations, such as sending "typing..." actions.

## Reactions (`pedro/brain/reactions/`)

-   **`messages_handler.py`**: The main message handler that orchestrates all other reactions. It receives incoming messages and triggers the appropriate reactions based on the message content.
-   **`default_pedro.py`**: The default reaction, which is triggered when no other specific reaction matches. It uses the LLM to generate a response based on the conversation history and user data.
-   **`agenda_commands.py`**: Handles all commands related to the agenda, such as `/agendar`, `/agenda`, `/aniversario`, and `/delete`.
-   **`complain_swearword.py`**: Reacts to messages containing swear words, either by critiquing the language or by sending a random message.
-   **`critic_or_praise.py`**: Handles commands like `/critique`, `/elogie`, `/simpatize`, and `/humilhe`, which use the LLM to generate a response that criticizes or praises a user.
-   **`emoji_reactions.py`**: Reacts to messages with emojis based on jejich content (e.g., political, congratulations, LGBT-related).
-   **`fact_check.py`**: Handles commands like `/refute`, `/fact`, and `/check`, which use the LLM to fact-check a statement from a Marxist perspective.
-   **`images_reactions.py`**: Reacts to images, either by analyzing them for political content or by generating a response based on the image and the conversation history.
-   **`misc_commands.py`**: Handles miscellaneous commands like `/me`, `/del`, `/data`, `/puto`, and `/version`.
-   **`random_reactions.py`**: Triggers random reactions based on user data and daily flags.
-   **`summary_reactions.py`**: Handles commands like `/tldr` and `/tlsr`, which use the LLM to summarize a conversation or a replied-to message.
-   **`weather_commands.py`**: Handles commands like `/previsao` and `/prev`, which provide weather forecasts for a specified location.

## Data Structures (`pedro/data_structures/`)

-   **`agenda.py`**: Defines the `Agenda` dataclass for storing agenda items.
-   **`bot_config.py`**: Defines the dataclasses for the bot's configuration, including `BotConfig`, `BotSecret`, and `Chats`.
-   **`chat_log.py`**: Defines the `ChatLog` dataclass for storing individual chat messages.
-   **`daily_flags.py`**: Defines the `DailyFlags` class for managing daily feature flags.
-   **`images.py`**: Defines the `MessageImage` and `MessageDocument` dataclasses for storing image and document data.
-   **`max_size_list.py`**: A custom list class with a maximum size.
-   **`telegram_message.py`**: Defines the dataclasses for Telegram messages, such as `Message`, `MessageReceived`, `Chat`, `From`, etc.
-   **`user_data.py`**: Defines the `UserData` dataclass for storing user information.

## Utils (`pedro/utils/`)

-   **`prompt_utils.py`**: Contains functions for creating prompts for the LLM.
-   **`text_utils.py`**: Contains utility functions for text manipulation, such as creating usernames, removing hashtags and emojis, and adjusting casing.
-   **`url_utils.py`**: Contains functions for extracting content from URLs, including YouTube transcripts and website paragraphs.
-   **`weather_utils.py`**: Contains functions for getting weather forecasts using the OpenWeatherMap API.

## Configuration

The bot is configured through two JSON files:

-   **`bot_configs.json`**: Contains the main configuration for the bot, such as the allowed chat IDs.
-   **`secrets.json`**: Contains the secret keys for the Telegram Bot API and the OpenAI API.

## How to Run

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure the bot**:
    -   Create `bot_configs.json` and `secrets.json` files based on the templates.
    -   Fill in the required information, such as the bot token, OpenAI key, and allowed chat IDs.
3.  **Run the bot**:
    ```bash
    python run.py
    ```
