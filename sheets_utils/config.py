"""
Configurações do Google Sheets.

O ID da planilha é lido do arquivo .env para que o código não fique preso a
uma planilha específica. O ID é o trecho da URL entre "/d/" e "/edit":
https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ID da planilha com os casos de teste (definido no .env)
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")

# Escopos de acesso solicitados ao Google na autorização OAuth:
# - spreadsheets: leitura e escrita nas planilhas (para gravar o ID do Jira de volta)
# - drive.metadata.readonly: leitura dos metadados (nome da planilha, abas)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

# Abas cujo nome começa com um destes prefixos são ignoradas no processamento.
# Útil para manter abas de rascunho, instruções ou modelos na mesma planilha.
PREFIXOS_ABAS_IGNORADAS = ("#", "_")
