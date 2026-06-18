"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

Publica o prompt no Hub usando a serialização nativa do LangChain.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

LOCAL_PROMPT_PATH = "prompts/bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def build_prompt_from_yaml(prompt_data: dict) -> ChatPromptTemplate:
    """Constrói um ChatPromptTemplate a partir do bloco YAML do prompt."""
    system_prompt = prompt_data.get("system_prompt", "").strip()
    user_prompt = prompt_data.get("user_prompt", "").strip()

    if not system_prompt:
        raise ValueError("system_prompt não encontrado ou vazio no YAML.")
    if not user_prompt:
        raise ValueError("user_prompt não encontrado ou vazio no YAML.")

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        prompt_template = build_prompt_from_yaml(prompt_data)

        print(f"Publicando prompt no LangSmith Hub: {prompt_name}")
        hub.push(
            repo_full_name=prompt_name,
            object=prompt_template,
            new_repo_is_public=True,
            new_repo_description=prompt_data.get("description"),
            tags=prompt_data.get("tags", []),
        )

        print(f"✅ Prompt publicado com sucesso: {prompt_name}")
        return True
    except Exception as e:
        error_text = str(e)

        if "Nothing to commit" in error_text:
            print("INFO: Prompt sem alterações desde o último commit no Hub.")
            print("✅ Repositório remoto já está atualizado.")
            return True

        print(f"❌ Erro ao publicar o prompt: {e}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    required_fields = [
        "description",
        "system_prompt",
        "user_prompt",
        "version",
        "techniques_applied",
    ]
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")

    if not str(prompt_data.get("system_prompt", "")).strip():
        errors.append("system_prompt está vazio")

    if not str(prompt_data.get("user_prompt", "")).strip():
        errors.append("user_prompt está vazio")

    system_prompt = str(prompt_data.get("system_prompt", ""))
    if "TODO" in system_prompt or "[TODO]" in system_prompt:
        errors.append("system_prompt ainda contém TODO")

    techniques = prompt_data.get("techniques_applied", [])
    if not isinstance(techniques, list):
        errors.append("techniques_applied deve ser uma lista")
    elif len(techniques) < 2:
        errors.append(
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"
        )

    return len(errors) == 0, errors


def main():
    """Função principal"""
    print_section_header("PUSH DO PROMPT PARA O LANGSMITH")

    required_vars = [
        "LANGSMITH_API_KEY",
        "LANGSMITH_ENDPOINT",
        "USERNAME_LANGSMITH_HUB",
    ]
    if not check_env_vars(required_vars):
        return 1

    yaml_data = load_yaml(LOCAL_PROMPT_PATH)
    if not yaml_data:
        print(f"❌ Não foi possível carregar o arquivo YAML: {LOCAL_PROMPT_PATH}")
        return 1

    prompt_data = yaml_data.get(PROMPT_KEY)
    if not prompt_data:
        print(f"❌ Chave '{PROMPT_KEY}' não encontrada no YAML.")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    prompt_name = f"{username}/{PROMPT_KEY}"

    success = push_prompt_to_langsmith(prompt_name, prompt_data)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
