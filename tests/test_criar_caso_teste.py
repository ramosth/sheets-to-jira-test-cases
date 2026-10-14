"""
Teste do fluxo de criação SEM acessar o Jira nem o Google: a aba da planilha
e as chamadas à API são substituídas por dublês (fakes/monkeypatch).

Verifica as regras de negócio do script:
- linhas com id_jira já preenchido não são recriadas (idempotência);
- linhas com id_pai inválido ou sem título são ignoradas;
- o ID criado é gravado de volta na planilha;
- casos automatizáveis passam por duas transições.
"""

import importlib
import sys

from jira_utils import jira_api_utils as jira


class AbaFalsa:
    """Imita um gspread.Worksheet guardando as escritas em memória."""

    def __init__(self, registros):
        self.title = "Login"
        self._registros = registros
        self.escritas = {}

    def get_all_records(self):
        return self._registros

    def update_cell(self, linha, coluna, valor):
        self.escritas[(linha, coluna)] = valor


def carregar_script():
    sys.path.insert(0, "scripts")
    return importlib.import_module("criar_caso_teste")


def test_processar_aba(monkeypatch):
    script = carregar_script()
    criados, transicoes = [], []

    def criar_falso(dados):
        criados.append(dados["titulo"])
        return f"QA-{100 + len(criados)}"

    monkeypatch.setattr(jira, "criar_caso_teste", criar_falso)
    monkeypatch.setattr(jira, "vincular_a_issue_pai", lambda *a: None)
    monkeypatch.setattr(jira, "atribuir_responsavel", lambda *a: None)
    monkeypatch.setattr(jira, "transicionar_status", lambda key, nome: transicoes.append((key, nome)))

    aba = AbaFalsa([
        {"id_pai": "QA-10", "id_jira": "", "titulo": "Novo caso", "tipo_execucao": "Automatizável"},
        {"id_pai": "QA-10", "id_jira": "QA-50", "titulo": "Já existe"},
        {"id_pai": "invalido", "id_jira": "", "titulo": "Pai inválido"},
        {"id_pai": "QA-10", "id_jira": "", "titulo": ""},
        {"id_pai": "QA-10", "id_jira": "", "titulo": "Caso manual", "tipo_execucao": "Manual"},
    ])

    total_criados, total_ignorados = script.processar_aba(aba, account_id="abc")

    assert criados == ["Novo caso", "Caso manual"]
    assert (total_criados, total_ignorados) == (2, 3)
    # id_jira é a 2ª coluna; linhas 2 e 6 da planilha receberam os novos IDs
    assert aba.escritas == {(2, 2): "QA-101", (6, 2): "QA-102"}
    # automatizável: duas transições; manual: só a primeira
    assert transicoes == [
        ("QA-101", "To write"), ("QA-101", "To automate"),
        ("QA-102", "To write"),
    ]
