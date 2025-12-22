# Internal
import math
from datetime import datetime

# Project
from pedro.brain.modules.chat_history import ChatHistory
from pedro.brain.modules.telegram import Telegram
from pedro.brain.modules.user_data_manager import UserDataManager
from pedro.brain.modules.llm import LLM
from pedro.brain.modules.task_list import TaskListManager
from pedro.data_structures.telegram_message import Message


async def trigger_add_personal(message: Message) -> bool:
    return message.text and message.text.lower().startswith("/tarefa ")


async def trigger_list_personal(message: Message) -> bool:
    return message.text and message.text.lower() == "/tarefas"


async def trigger_add_group(message: Message) -> bool:
    return message.text and message.text.lower().startswith("/tarefa_grupo ")


async def trigger_list_group(message: Message) -> bool:
    return message.text and message.text.lower() == "/tarefas_grupo"


async def trigger_complete(message: Message) -> bool:
    return message.text and message.text.lower().startswith("/concluir ")


async def task_commands_reaction(
    message: Message,
    history: ChatHistory,
    telegram: Telegram,
    user_data: UserDataManager,
    task_list: TaskListManager,
    llm: LLM,
) -> None:
    # Check which command was triggered
    add_personal = await trigger_add_personal(message)
    list_personal = await trigger_list_personal(message)
    add_group = await trigger_add_group(message)
    list_group = await trigger_list_group(message)
    complete = await trigger_complete(message)

    if not (add_personal or list_personal or add_group or list_group or complete):
        return

    # Split the message text into words
    message_split = message.text.split(maxsplit=1)

    # Handle /tarefa command (add personal task)
    if add_personal:
        if len(message_split) < 2:
            await telegram.send_message(
                message_text="<b>Exemplo para adicionar tarefa pessoal:</b>\n/tarefa Comprar leite",
                chat_id=message.chat.id,
                reply_to=message.message_id,
                parse_mode="HTML"
            )
        else:
            description = message_split[1].strip()
            
            task_item = task_list.add_task_item(
                description=description,
                created_by=message.from_.id,
                for_chat=message.chat.id,
                is_group_task=False
            )

            await telegram.send_message(
                message_text=f"<b>Tarefa pessoal adicionada:</b>\n{description}\n\n<b>ID:</b> {task_item.id}",
                chat_id=message.chat.id,
                reply_to=message.message_id,
                parse_mode="HTML"
            )

    # Handle /tarefas command (list personal tasks)
    elif list_personal:
        task_items = task_list.get_task_items_for_user(message.from_.id)

        if not task_items:
            await telegram.send_message(
                message_text="Você não tem tarefas pessoais neste chat.",
                chat_id=message.chat.id,
                reply_to=message.message_id,
                parse_mode="HTML"
            )
            return

        # Format the task items for display
        task_texts = []
        for item in task_items:
            task_texts.append(
                f"<b>ID {item.id}</b> - {item.description}"
            )

        # Split the task items into multiple messages if needed
        message_len = 8
        tasks = []
        last_idx = 0
        messages_count = math.ceil(len(task_texts) / message_len)

        for i in range(messages_count):
            tasks.append('\n'.join(task_texts[last_idx:last_idx + message_len]))
            last_idx += message_len

        # Send the messages
        for i, entry in enumerate(tasks):
            await telegram.send_message(
                message_text=f"<b>Suas tarefas pessoais</b> - {i + 1}/{len(tasks)}\n\n{entry}",
                chat_id=message.chat.id,
                parse_mode="HTML"
            )

    # Handle /tarefa_grupo command (add group task)
    elif add_group:
        if len(message_split) < 2:
            await telegram.send_message(
                message_text="<b>Exemplo para adicionar tarefa do grupo:</b>\n/tarefa_grupo Limpar o chat",
                chat_id=message.chat.id,
                reply_to=message.message_id,
                parse_mode="HTML"
            )
        else:
            description = message_split[1].strip()
            
            task_item = task_list.add_task_item(
                description=description,
                created_by=message.from_.id,
                for_chat=message.chat.id,
                is_group_task=True
            )

            await telegram.send_message(
                message_text=f"<b>Tarefa do grupo adicionada:</b>\n{description}\n\n<b>ID:</b> {task_item.id}",
                chat_id=message.chat.id,
                reply_to=message.message_id,
                parse_mode="HTML"
            )

    # Handle /tarefas_grupo command (list group tasks)
    elif list_group:
        task_items = task_list.get_task_items_for_group(message.chat.id)

        if not task_items:
            await telegram.send_message(
                message_text="Não há tarefas do grupo neste chat.",
                chat_id=message.chat.id,
                reply_to=message.message_id,
                parse_mode="HTML"
            )
            return

        # Format the task items for display
        task_texts = []
        for item in task_items:
            # Get the creator's name from user_data if available
            creator_name = f"ID {item.created_by}"
            
            task_texts.append(
                f"<b>ID {item.id}</b> - {item.description} - <b>Criada por:</b> {creator_name}"
            )

        # Split the task items into multiple messages if needed
        message_len = 8
        tasks = []
        last_idx = 0
        messages_count = math.ceil(len(task_texts) / message_len)

        for i in range(messages_count):
            tasks.append('\n'.join(task_texts[last_idx:last_idx + message_len]))
            last_idx += message_len

        # Send the messages
        for i, entry in enumerate(tasks):
            await telegram.send_message(
                message_text=f"<b>Tarefas do grupo</b> - {i + 1}/{len(tasks)}\n\n{entry}",
                chat_id=message.chat.id,
                parse_mode="HTML"
            )

    # Handle /concluir command (complete/delete task)
    elif complete:
        msg_split = message.text.split()

        if len(msg_split) != 2:
            await telegram.send_message(
                message_text="<b>Para concluir uma tarefa:</b>\n/concluir <id>",
                chat_id=message.chat.id,
                reply_to=message.message_id,
                parse_mode="HTML"
            )
        else:
            item_id = msg_split[1]
            item = task_list.get_task_item_by_id(item_id)

            if not item:
                await telegram.send_message(
                    message_text=f"Não encontrei a tarefa com ID {item_id}. Use /tarefas ou /tarefas_grupo para ver os IDs corretos.",
                    chat_id=message.chat.id,
                    reply_to=message.message_id,
                    parse_mode="HTML"
                )
                return

            # Check permissions
            # For personal tasks, only the creator can complete them
            # For group tasks, anyone in the group can complete them
            if not item.is_group_task and item.created_by != message.from_.id:
                await telegram.send_message(
                    message_text=f"Você não tem permissão para concluir esta tarefa. Apenas o criador pode concluir tarefas pessoais.",
                    chat_id=message.chat.id,
                    reply_to=message.message_id,
                    parse_mode="HTML"
                )
                return

            # Delete the task
            if task_list.delete_task_item(item_id):
                task_type = "do grupo" if item.is_group_task else "pessoal"
                await telegram.send_message(
                    message_text=f"<b>Tarefa {task_type} concluída e removida:</b>\n{item.description}",
                    chat_id=message.chat.id,
                    reply_to=message.message_id,
                    parse_mode="HTML"
                )
            else:
                await telegram.send_message(
                    message_text=f"Erro ao concluir a tarefa {item_id}. Tente novamente.",
                    chat_id=message.chat.id,
                    reply_to=message.message_id,
                    parse_mode="HTML"
                )
