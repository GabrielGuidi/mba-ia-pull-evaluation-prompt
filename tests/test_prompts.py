"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
import re
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    """Carrega o prompt v2 usado pelos testes."""
    data = load_prompts(str(PROMPT_FILE))
    assert isinstance(data, dict), "Arquivo YAML deve carregar como dicionário"
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada"
    return data[PROMPT_KEY]


@pytest.fixture(scope="module")
def system_prompt(prompt_data):
    """Retorna o system prompt do YAML."""
    return prompt_data.get("system_prompt", "")


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data, system_prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        is_valid, errors = validate_prompt_structure(prompt_data)

        assert isinstance(system_prompt, str), "system_prompt deve ser texto"
        assert system_prompt.strip(), "system_prompt está vazio"
        assert is_valid, f"Estrutura inválida do prompt: {errors}"

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        prompt_lower = system_prompt.lower()

        assert "você é" in prompt_lower, "Prompt deve definir persona explicitamente"
        assert re.search(
            r"product manager|business analyst|analyst|gerente de produto",
            system_prompt,
            re.IGNORECASE,
        ), "Prompt deve mencionar uma persona de produto/análise"

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        prompt_lower = system_prompt.lower()

        assert "markdown" in prompt_lower, "Prompt deve exigir formato Markdown"
        assert "como <tipo de usuário" in prompt_lower, "Prompt deve exigir User Story padrão"
        assert "critérios de aceitação" in prompt_lower, (
            "Prompt deve exigir critérios de aceitação"
        )

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        prompt_lower = system_prompt.lower()
        entradas = re.findall(r"\bentrada:", prompt_lower)
        saidas = re.findall(r"\bsaída:", prompt_lower)

        assert "exemplos few-shot" in prompt_lower, "Prompt deve mencionar few-shot"
        assert len(entradas) >= 2, "Prompt deve conter ao menos 2 exemplos de entrada"
        assert len(saidas) >= 2, "Prompt deve conter ao menos 2 exemplos de saída"

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        full_text = yaml.dump(prompt_data, allow_unicode=True)

        assert "[TODO]" not in full_text
        assert re.search(r"\bTODO\b", full_text, flags=re.IGNORECASE) is None

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])

        assert isinstance(techniques, list), "techniques_applied deve ser uma lista"
        assert len(techniques) >= 2, "Mínimo de 2 técnicas requeridas"
        assert "Few-shot Learning" in techniques, "Few-shot Learning é obrigatório"
        assert any(
            technique in techniques
            for technique in ["Role Prompting", "Skeleton of Thought"]
        ), "Prompt deve aplicar Role Prompting ou Skeleton of Thought"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
