# Internal
from typing import Any, Dict, Optional

# Project
from pedro.brain.agent.tools.base import Tool
from pedro.brain.modules.user_data_manager import UserDataManager


class ManageCustomBehaviorTool(Tool):
    """
    Tool for managing custom behaviors for specific users.
    Allows the LLM to configure how Pedro should act with a target user,
    or clear a user's custom behavior when requested.
    """

    def __init__(self, requesting_user_id: int, user_data_manager: UserDataManager):
        self.requesting_user_id = requesting_user_id
        self.user_data_manager = user_data_manager

    @property
    def name(self) -> str:
        return "manage_custom_behavior"

    @property
    def description(self) -> str:
        return (
            "Permite alterar a forma como Pedro age com um usuário específico (definindo um comportamento customizado) "
            "ou limpar/remover o comportamento customizado de um usuário (definindo como nulo/parando de agir daquela forma). "
            "Use esta ferramenta quando o usuário solicitar para você (Pedro) agir de uma determinada maneira com outra pessoa "
            "(ex: 'trate o @fulano de forma romântica', 'aja com diogo como se ele fosse seu chefe') ou parar de agir assim "
            "(ex: 'pare de tratar o fulano daquele jeito', 'limpa o comportamento customizado do @fulano')."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target_user": {
                    "type": "string",
                    "description": "O username (ex: '@diogo' ou 'diogo') ou primeiro nome do usuário que terá o comportamento alterado."
                },
                "behavior": {
                    "type": "string",
                    "description": "Instruções de como o Pedro deve agir com o usuário. Se o objetivo for limpar, remover ou parar de agir de determinada maneira, deixe este campo vazio, nulo ou defina como ''."
                }
            },
            "required": ["target_user"]
        }

    async def execute(self, target_user: str, behavior: Optional[str] = None) -> str:
        """
        Execute the custom behavior management action.

        Args:
            target_user: The username or first name of the target user.
            behavior: Optional behavior description. If empty or None, custom behavior is cleared.

        Returns:
            String with the result of the operation.
        """
        try:
            # Check authorization of requesting user
            requesting_user = self.user_data_manager.get_user_data(self.requesting_user_id)
            access_level = requesting_user.access_level if requesting_user is not None else 1

            if access_level < 1:
                return "erro: você não tem autorização para isso"

            # Clean target_user string
            target_clean = target_user.strip()
            if target_clean.startswith('@'):
                target_clean = target_clean[1:]

            target_lower = target_clean.lower()

            # Retrieve all users to find a match
            all_users = self.user_data_manager.get_all_user_opinions()
            target_user_data = None

            # 1. Exact username match
            for u in all_users:
                if u.username and u.username.lower() == target_lower:
                    target_user_data = u
                    break

            # 2. Exact first name match
            if not target_user_data:
                for u in all_users:
                    if u.first_name and u.first_name.lower() == target_lower:
                        target_user_data = u
                        break

            # 3. Fuzzy match
            if not target_user_data:
                matches = self.user_data_manager.get_users_by_text_match(target_clean, threshold=0.7)
                if matches:
                    target_user_data = matches[0]

            if not target_user_data:
                return f"erro: não encontrei o usuário '{target_user}'"

            # Determine if we should set or clear behavior
            is_clear = not behavior or behavior.strip() == "" or behavior.lower() in ("null", "none", "limpar", "clear")

            name_str = target_user_data.username or target_user_data.first_name or str(target_user_data.user_id)
            if not name_str.startswith('@') and target_user_data.username:
                name_str = '@' + name_str

            if is_clear:
                # Clear behavior
                self.user_data_manager.database.update(
                    self.user_data_manager.table_name,
                    {"custom_behavior": None},
                    {"user_id": target_user_data.user_id}
                )
                return f"sucesso: o comportamento customizado de {name_str} foi limpo"
            else:
                # Set behavior
                behavior_clean = behavior.strip()
                self.user_data_manager.database.update(
                    self.user_data_manager.table_name,
                    {"custom_behavior": behavior_clean},
                    {"user_id": target_user_data.user_id}
                )
                return f"sucesso: agora vou agir com {name_str} da seguinte maneira: {behavior_clean}"

        except Exception as e:
            return f"erro ao executar ação: {str(e)}"
