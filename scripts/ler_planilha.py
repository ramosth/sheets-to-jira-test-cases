"""
Testa a conexão com o Google Sheets e mostra o conteúdo das abas.

É o primeiro script a rodar: na primeira execução ele abre o navegador para
autorizar o acesso e salva o token em auth/token.pickle.

Uso:
    python scripts/ler_planilha.py
"""

import gspread

import _bootstrap  # noqa: F401  (ajusta o sys.path)

from sheets_utils import planilha as sheets


def main():
    try:
        planilha = sheets.abrir_planilha()
    except gspread.exceptions.SpreadsheetNotFound:
        print("❌ Planilha não encontrada. Confira o SPREADSHEET_ID e se sua conta tem acesso.")
        return
    except gspread.exceptions.APIError as erro:
        print(f"❌ Erro na API do Google: {erro}")
        return

    for aba in planilha.worksheets():
        ignorada = " (ignorada pelos scripts)" if aba not in sheets.abas_para_processar(planilha) else ""
        print(f"\n{'=' * 50}\nAba: {aba.title}{ignorada}\n{'=' * 50}")

        df = sheets.ler_aba(aba)
        if df.empty:
            print("  (aba vazia)")
            continue
        for indice, linha in df.iterrows():
            print(f"Linha {indice + 2}: [{linha.get('id_jira') or 'sem ID'}] {linha.get('titulo', '')}")


if __name__ == "__main__":
    main()
