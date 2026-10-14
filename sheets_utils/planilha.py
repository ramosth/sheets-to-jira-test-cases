"""
Leitura e escrita da planilha de casos de teste.

Formato esperado (uma linha por caso de teste, uma aba por história/módulo):

| id_pai | id_jira | titulo | objetivo | pre_condicoes | descricao | tipo_execucao | tipo_teste | componentes | ultima_atualizacao |

- id_pai:      história/requisito ao qual o caso será vinculado (ex.: QA-10)
- id_jira:     preenchido AUTOMATICAMENTE após a criação (ex.: QA-123)
- descricao:   cenário em Gherkin (Dado / Quando / Então)
- ultima_atualizacao: preenchida automaticamente na edição

Os nomes das colunas são normalizados (minúsculas, sem acento e sem espaços
nas pontas), então "Pré Condições " e "pre_condicoes" são tratados igual
desde que usem o mesmo separador.
"""

import re

import pandas as pd
from unidecode import unidecode

from sheets_utils.auth import obter_cliente_gspread
from sheets_utils.config import PREFIXOS_ABAS_IGNORADAS, SPREADSHEET_ID

# Formato de chave de issue do Jira: PROJETO-NÚMERO (ex.: QA-10, APP2-301)
PADRAO_CHAVE_JIRA = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")


def normalizar_coluna(nome):
    """'Pré Condições ' -> 'pre condicoes'."""
    return unidecode(str(nome).strip().lower())


def chave_jira_valida(valor):
    """Retorna True se o valor tem o formato de chave do Jira (ex.: QA-10)."""
    return bool(PADRAO_CHAVE_JIRA.match(str(valor or "").strip()))


def abrir_planilha(spreadsheet_id=None):
    """
    Abre a planilha configurada no .env (ou a informada).

    Returns:
        gspread.Spreadsheet
    """
    spreadsheet_id = spreadsheet_id or SPREADSHEET_ID
    if not spreadsheet_id:
        raise ValueError("❌ SPREADSHEET_ID não definido no .env.")
    planilha = obter_cliente_gspread().open_by_key(spreadsheet_id)
    print(f"✓ Conectado à planilha: {planilha.title}")
    return planilha


def abas_para_processar(planilha):
    """
    Lista as abas da planilha, ignorando as de rascunho/instrução
    (nome começando com '#' ou '_').
    """
    return [
        aba for aba in planilha.worksheets()
        if not aba.title.startswith(PREFIXOS_ABAS_IGNORADAS)
    ]


def ler_aba(aba):
    """
    Lê uma aba e devolve um DataFrame com colunas normalizadas.
    Garante que as colunas id_jira e ultima_atualizacao existam.
    """
    df = pd.DataFrame(aba.get_all_records())
    if df.empty:
        return df

    df.columns = [normalizar_coluna(c) for c in df.columns]
    for coluna in ("id_jira", "ultima_atualizacao"):
        if coluna not in df.columns:
            df[coluna] = ""
    df["id_jira"] = df["id_jira"].astype(str).replace("nan", "")
    return df


def linha_para_dados(linha):
    """
    Converte uma linha da planilha no dicionário usado pelo jira_api_utils.
    Os valores padrão cobrem colunas opcionais deixadas em branco.
    """
    texto = lambda coluna, padrao="": str(linha.get(coluna, "") or padrao).strip()
    return {
        "titulo": texto("titulo"),
        "objetivo": texto("objetivo"),
        "pre_condicoes": texto("pre_condicoes"),
        "cenario": texto("descricao"),
        "tipo_execucao": texto("tipo_execucao", "Automatizável"),
        "tipo_teste": texto("tipo_teste", "Funcional"),
        "componentes": texto("componentes"),
    }


def escrever_celula(aba, df, indice_linha, coluna, valor):
    """
    Escreve um valor de volta na planilha.

    Args:
        indice_linha: índice da linha no DataFrame (0 = primeira linha de dados).
                      Na planilha isso corresponde à linha indice + 2, porque a
                      linha 1 é o cabeçalho e o gspread começa a contar em 1.
    """
    numero_linha = indice_linha + 2
    numero_coluna = df.columns.get_loc(coluna) + 1
    aba.update_cell(numero_linha, numero_coluna, valor)
