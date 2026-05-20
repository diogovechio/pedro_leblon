import json
import os
from typing import Optional


def find_invalid_jsons(chat_logs_dir: str = "database/chat_logs") -> list[str]:
    """
    Lê todos os arquivos .json na pasta chat_logs (incluindo subpastas)
    e retorna uma lista com os caminhos dos JSONs inválidos.

    Args:
        chat_logs_dir: Caminho para a pasta de chat_logs.
                       Padrão: "database/chat_logs".

    Returns:
        Lista de caminhos (strings) dos arquivos JSON que não puderam
        ser parseados corretamente.
    """
    invalid_files: list[str] = []

    for root, _, files in os.walk(chat_logs_dir):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                invalid_files.append(filepath)

    return invalid_files


def find_invalid_jsons_detailed(
    chat_logs_dir: str = "database/chat_logs",
) -> list[dict[str, str]]:
    """
    Versão detalhada que retorna o caminho e a mensagem de erro
    para cada JSON inválido.

    Args:
        chat_logs_dir: Caminho para a pasta de chat_logs.

    Returns:
        Lista de dicts com as chaves "path" e "error".
    """
    invalid_files: list[dict[str, str]] = []

    for root, _, files in os.walk(chat_logs_dir):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                invalid_files.append({"path": filepath, "error": str(e)})

    return invalid_files


if __name__ == "__main__":
    invalids = find_invalid_jsons_detailed()
    if invalids:
        print(f"Encontrados {len(invalids)} arquivo(s) JSON inválido(s):\n")
        for item in invalids:
            print(f"  ❌ {item['path']}")
            print(f"     Erro: {item['error']}\n")
    else:
        print("✅ Todos os arquivos JSON são válidos.")
