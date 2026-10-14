"""
Testes unitários das partes que não dependem de rede: validação de chaves
do Jira, normalização das colunas da planilha e montagem do payload.

Rodar com:  pytest -v
"""

import pytest

from jira_utils import config
from jira_utils import jira_api_utils as jira
from sheets_utils import planilha as sheets


@pytest.mark.parametrize("valor", ["QA-1", "QA-123", "APP2-301"])
def test_chave_jira_valida(valor):
    assert sheets.chave_jira_valida(valor)


@pytest.mark.parametrize("valor", ["", None, "qa-1", "QA", "QA-", "123-QA", "QA 12"])
def test_chave_jira_invalida(valor):
    assert not sheets.chave_jira_valida(valor)


def test_normalizar_coluna_remove_acento_e_espacos():
    assert sheets.normalizar_coluna("  Pré Condições ") == "pre condicoes"


def test_linha_para_dados_aplica_padroes():
    dados = sheets.linha_para_dados({"titulo": " Login válido ", "descricao": "Dado ..."})
    assert dados["titulo"] == "Login válido"
    assert dados["cenario"] == "Dado ..."
    assert dados["tipo_execucao"] == "Automatizável"
    assert dados["tipo_teste"] == "Funcional"


def test_separar_componentes():
    assert jira.separar_componentes("Front, API ,") == [{"name": "Front"}, {"name": "API"}]
    assert jira.separar_componentes("") == []


def test_descricao_tem_bloco_gherkin():
    doc = jira.montar_descricao("obj", "pre", "Dado que...")
    bloco = doc["content"][-1]
    assert bloco["type"] == "codeBlock"
    assert bloco["attrs"]["language"] == "gherkin"
    assert bloco["content"][0]["text"] == "Dado que..."


def test_campos_personalizados_vem_da_configuracao(monkeypatch):
    monkeypatch.setattr(config, "CAMPO_TIPO_EXECUCAO", "customfield_1")
    monkeypatch.setattr(config, "CAMPO_TIPO_TESTE", "")  # não configurado
    campos = jira.montar_campos_caso_teste(
        {"titulo": "T", "tipo_execucao": "Manual", "tipo_teste": "Funcional", "componentes": "Front"}
    )
    assert campos["customfield_1"] == {"value": "Manual"}
    assert "customfield_2" not in campos
    assert campos["components"] == [{"name": "Front"}]
