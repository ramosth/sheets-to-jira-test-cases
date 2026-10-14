"""
Configurações do Jira, todas lidas do arquivo .env.

Cada instância do Jira tem seus próprios IDs de campos personalizados
(customfield_XXXXX), de tipo de issue e nomes de transição. Por isso nada
disso fica fixo no código: basta ajustar o .env para apontar para outro
projeto ou outra empresa.

Como descobrir os IDs dos campos personalizados:
GET {JIRA_URL}/rest/api/3/field  -> procure pelo nome do campo e copie o "id".
"""

import os

from dotenv import load_dotenv

load_dotenv()

# --- Conexão ---------------------------------------------------------------
JIRA_URL = os.getenv("JIRA_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

# A API do Jira Cloud usa autenticação Basic com e-mail + token de API.
AUTH = (JIRA_EMAIL, JIRA_API_TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

# --- Projeto ---------------------------------------------------------------
# Chave do projeto onde os casos de teste serão criados (ex.: QA -> QA-123)
PROJECT_KEY = os.getenv("PROJECT_KEY", "").strip()

# ID do tipo de issue "Caso de Teste" no seu Jira
ISSUE_TYPE_ID = os.getenv("JIRA_ISSUE_TYPE_ID", "")

# Nome do tipo de vínculo entre a história (issue pai) e o caso de teste
LINK_TYPE_NAME = os.getenv("JIRA_LINK_TYPE_NAME", "Casos de Teste")

# --- Campos personalizados -------------------------------------------------
CAMPO_TIPO_EXECUCAO = os.getenv("JIRA_FIELD_TIPO_EXECUCAO", "")  # lista: Manual / Automatizável
CAMPO_TIPO_TESTE = os.getenv("JIRA_FIELD_TIPO_TESTE", "")        # lista: Funcional, Regressão...
CAMPO_OBJETIVO = os.getenv("JIRA_FIELD_OBJETIVO", "")            # texto rico
CAMPO_PRE_CONDICOES = os.getenv("JIRA_FIELD_PRE_CONDICOES", "")  # texto rico

# --- Workflow --------------------------------------------------------------
# Transições aplicadas logo após a criação, conforme o tipo de execução.
TRANSICAO_A_ESCREVER = os.getenv("TRANSICAO_A_ESCREVER", "To write")
TRANSICAO_A_AUTOMATIZAR = os.getenv("TRANSICAO_A_AUTOMATIZAR", "To automate")


def validar_configuracao():
    """
    Garante que as variáveis obrigatórias foram preenchidas antes de qualquer
    chamada à API, para falhar cedo com uma mensagem clara.
    """
    obrigatorias = {
        "JIRA_URL": JIRA_URL,
        "JIRA_EMAIL": JIRA_EMAIL,
        "JIRA_API_TOKEN": JIRA_API_TOKEN,
        "PROJECT_KEY": PROJECT_KEY,
        "JIRA_ISSUE_TYPE_ID": ISSUE_TYPE_ID,
    }
    faltando = [nome for nome, valor in obrigatorias.items() if not valor]
    if faltando:
        raise ValueError(
            "❌ Variáveis ausentes no .env: " + ", ".join(faltando)
            + ". Use o .env.example como modelo."
        )
