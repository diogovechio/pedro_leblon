# Internal
from typing import Any, Dict, Optional

# Project
from pedro.brain.agent.tools.base import Tool
from pedro.brain.modules.user_data_manager import UserDataManager


class RememberOpinionTool(Tool):
    """
    Tool for remembering an opinion/fact about another user.
    Only allows users with access_level >= 1 to use it.
    """

    def __init__(self, requesting_user_id: int, user_data_manager: UserDataManager):
        self.requesting_user_id = requesting_user_id
        self.user_data_manager = user_data_manager

    @property
    def name(self) -> str:
        return "remember_opinion"

    @property
    def description(self) -> str:
        return (
            "Permite salvar uma opinião, fato ou informação sobre um usuário específico na lista de opiniões dele. "
            "Use esta ferramenta quando um usuário pedir para você (Pedro) lembrar de algo sobre outra pessoa "
            "(ex: 'lembra que o @fulano torce para o flamengo', 'lembra que o diogo gosta de café')."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target_user": {
                    "type": "string",
                    "description": "O username (ex: '@diogo' ou 'diogo') ou primeiro nome do usuário que terá a informação associada."
                },
                "opinion": {
                    "type": "string",
                    "description": "A informação, opinião ou fato a ser lembrado (ex: 'gosta de café', 'torce para o flamengo')."
                }
            },
            "required": ["target_user", "opinion"]
        }

    async def execute(self, target_user: str, opinion: str) -> str:
        """
        Execute the remember opinion action.

        Args:
            target_user: The username or first name of the target user.
            opinion: The opinion or fact to remember.

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

            # Clean opinion string
            opinion_clean = opinion.strip()
            if not opinion_clean:
                return "erro: a informação a ser lembrada não pode ser vazia"

            # Add opinion (respects max_opinions inside add_opinion)
            updated_user = self.user_data_manager.add_opinion(
                opinion=opinion_clean,
                user_id=target_user_data.user_id
            )

            if updated_user is None:
                return "erro ao salvar a opinião"

            name_str = target_user_data.username or target_user_data.first_name or str(target_user_data.user_id)
            if not name_str.startswith('@') and target_user_data.username:
                name_str = '@' + name_str

            return f"sucesso: lembrei que {name_str} {opinion_clean}"

        except Exception as e:
            return f"erro ao executar ação: {str(e)}"
