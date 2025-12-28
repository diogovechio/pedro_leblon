# Internal
from typing import Any, Dict
from pedro.brain.agent.tools.base import Tool
from pedro.brain.modules.task_list import TaskListManager


class TaskListTool(Tool):
    """
    Tool for managing task lists (personal and group tasks).
    Allows the LLM to add and list tasks, but instructs users to use /concluir for completion.
    """
    
    def __init__(self, user_id: int, chat_id: int, task_list_manager: TaskListManager):
        self.user_id = user_id
        self.chat_id = chat_id
        self.task_manager = task_list_manager

    @property
    def name(self) -> str:
        return "manage_tasks"

    @property
    def description(self) -> str:
        return (
            "Gerencia listas de tarefas pessoais e do grupo. "
            "Use esta ferramenta quando o usuário pedir para adicionar, listar ou concluir tarefas. "
            "Tarefas pessoais são acessíveis de qualquer chat. "
            "Tarefas do grupo são específicas deste chat. "
            "Por padrão, usuários mencionarão tarefas pessoais, apenas adicione ou liste do grupo caso o "
            "usuário especifique que é para o grupo ou para todos. "
            "Para concluir uma tarefa, use a ação 'complete_task' com o ID da tarefa."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add_personal", "list_personal", "add_group", "list_group", "complete_task"],
                    "description": (
                        "Ação a realizar: "
                        "'add_personal' para adicionar tarefa pessoal, "
                        "'list_personal' para listar tarefas pessoais, "
                        "'add_group' para adicionar tarefa do grupo, "
                        "'list_group' para listar tarefas do grupo, "
                        "'complete_task' para concluir uma tarefa"
                    )
                },
                "description": {
                    "type": "string",
                    "description": "Descrição da tarefa (obrigatório apenas para add_personal e add_group)"
                },
                "task_id": {
                    "type": "string",
                    "description": "ID da tarefa (obrigatório apenas para complete_task)"
                }
            },
            "required": ["action"]
        }

    async def execute(self, action: str, description: str = None, task_id: str = None) -> str:
        """
        Execute task management actions.
        
        Args:
            action: The action to perform (add_personal, list_personal, add_group, list_group, complete_task)
            description: Task description (required for add actions)
            task_id: Task ID (required for complete_task action)
            
        Returns:
            String with the result of the operation
        """
        try:
            if action == "add_personal":
                if not description:
                    return "Erro: descrição da tarefa é obrigatória para adicionar."
                
                task_item = self.task_manager.add_task_item(
                    description=description,
                    created_by=self.user_id,
                    for_chat=self.chat_id,
                    is_group_task=False
                )
                return f"Tarefa pessoal adicionada com sucesso! ID: {task_item.id} - {description}"
            
            elif action == "list_personal":
                task_items = self.task_manager.get_task_items_for_user(self.user_id)
                
                if not task_items:
                    return "Você não tem tarefas pessoais."
                
                result = "Suas tarefas pessoais:\n"
                for item in task_items:
                    result += f"- ID {item.id}: {item.description}\n"
                
                return result
            
            elif action == "add_group":
                if not description:
                    return "Erro: descrição da tarefa é obrigatória para adicionar."
                
                task_item = self.task_manager.add_task_item(
                    description=description,
                    created_by=self.user_id,
                    for_chat=self.chat_id,
                    is_group_task=True
                )
                return f"Tarefa do grupo adicionada com sucesso! ID: {task_item.id} - {description}"
            
            elif action == "list_group":
                task_items = self.task_manager.get_task_items_for_group(self.chat_id)
                
                if not task_items:
                    return "Não há tarefas do grupo neste chat."
                
                result = "Tarefas do grupo:\n"
                for item in task_items:
                    result += f"- ID {item.id}: {item.description}\n"
                
                return result
            
            elif action == "complete_task":
                if not task_id:
                    return "Erro: ID da tarefa é obrigatório para concluir."
                
                # Get the task to check permissions
                task_item = self.task_manager.get_task_item_by_id(task_id)
                
                if not task_item:
                    return f"Tarefa com ID {task_id} não encontrada."
                
                # Check permissions
                # For personal tasks, only the creator can complete them
                # For group tasks, anyone in the group can complete them
                if not task_item.is_group_task and task_item.created_by != self.user_id:
                    return f"Você não tem permissão para concluir esta tarefa. Apenas o criador pode concluir tarefas pessoais."
                
                # Delete the task
                if self.task_manager.delete_task_item(task_id):
                    task_type = "do grupo" if task_item.is_group_task else "pessoal"
                    return f"Tarefa {task_type} concluída e removida: {task_item.description}"
                else:
                    return f"Erro ao concluir a tarefa {task_id}."
            
            else:
                return f"Ação inválida: {action}"
                
        except Exception as e:
            return f"Erro ao executar ação: {str(e)}"
