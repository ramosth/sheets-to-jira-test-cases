"""
Atualiza no Jira os casos de teste que foram alterados na planilha.

A planilha continua sendo a fonte da verdade: ajuste o texto do caso na
planilha e rode este script informando os IDs. O título, a descrição, os
campos personalizados e os componentes são reenviados ao Jira, e a coluna
`ultima_atualizacao` recebe a data e a hora da edição.

Uso:
    python scripts/editar_casos_testes.py QA-123 QA-124
    python scripts/editar_casos_testes.py          # pergunta os IDs no terminal

Também permite excluir casos criados por engano (ação permanente):
    python scripts/editar_casos_testes.py --excluir QA-130 QA-131
"""

import argparse
from datetime import datetime

import _bootstrap  # noqa: F401  (ajusta o sys.path)

from jira_utils import config
from jira_utils import jira_api_utils as jira
from sheets_utils import planilha as sheets


def ler_ids_do_terminal():
    """Pede ao usuário os IDs separados por vírgula."""
    entrada = input("📝 Informe os IDs do Jira que deseja atualizar (separados por vírgula): ")
    return [i.strip().upper() for i in entrada.split(",") if i.strip()]


def atualizar(ids):
    """Procura cada ID em todas as abas e reenvia os dados para o Jira."""
    pendentes = set(ids)
    atualizados = 0

    for aba in sheets.abas_para_processar(sheets.abrir_planilha()):
        df = sheets.ler_aba(aba)
        if df.empty:
            continue

        for indice, linha in df.iterrows():
            issue_key = str(linha.get("id_jira", "")).strip().upper()
            if issue_key not in pendentes:
                continue

            if jira.atualizar_caso_teste(issue_key, sheets.linha_para_dados(linha)):
                agora = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                df.at[indice, "ultima_atualizacao"] = agora
                sheets.escrever_celula(aba, df, indice, "ultima_atualizacao", agora)
                atualizados += 1
            pendentes.discard(issue_key)

    if pendentes:
        print(f"⚠️ IDs não encontrados na planilha: {', '.join(sorted(pendentes))}")
    print(f"\n✅ Total de casos de teste atualizados: {atualizados}")


def main():
    parser = argparse.ArgumentParser(description="Atualiza ou exclui casos de teste no Jira.")
    parser.add_argument("ids", nargs="*", help="IDs do Jira (ex.: QA-123 QA-124)")
    parser.add_argument("--excluir", action="store_true", help="exclui as issues informadas")
    args = parser.parse_args()

    config.validar_configuracao()
    ids = [i.upper() for i in args.ids] or ler_ids_do_terminal()
    if not ids:
        print("Nenhum ID informado.")
        return

    if args.excluir:
        confirmacao = input(f"⚠️ Excluir permanentemente {', '.join(ids)}? (s/N) ")
        if confirmacao.strip().lower() == "s":
            jira.excluir_issues(ids)
        return

    atualizar(ids)


if __name__ == "__main__":
    main()
