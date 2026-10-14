"""
Cria casos de teste em massa no Jira a partir do Google Sheets.

Para cada aba da planilha e cada linha ainda sem `id_jira`:
  1. valida o ID da história pai e o título;
  2. cria o caso de teste no Jira com objetivo, pré-condição e cenário Gherkin;
  3. vincula o caso à história pai (rastreabilidade);
  4. atribui o caso a quem executou o script;
  5. move o card no workflow conforme o tipo de execução;
  6. grava o ID gerado de volta na planilha.

Como a coluna id_jira é preenchida ao final, rodar o script de novo NÃO
duplica casos: linhas que já têm ID são ignoradas.

Uso:
    python scripts/criar_caso_teste.py
"""

import _bootstrap  # noqa: F401  (ajusta o sys.path)

from jira_utils import config
from jira_utils import jira_api_utils as jira
from sheets_utils import planilha as sheets


def transicionar_conforme_execucao(issue_key, tipo_execucao):
    """
    Casos manuais vão para "To write". Casos automatizáveis passam por
    "To write" e seguem para "To automate", entrando direto na fila de
    automação do time.
    """
    tipo = tipo_execucao.strip().lower()
    if tipo in ("manual", "automatizável", "automatizavel"):
        jira.transicionar_status(issue_key, config.TRANSICAO_A_ESCREVER)
    if tipo in ("automatizável", "automatizavel"):
        jira.transicionar_status(issue_key, config.TRANSICAO_A_AUTOMATIZAR)


def processar_aba(aba, account_id):
    """Cria os casos de teste de uma aba e devolve (criados, ignorados)."""
    print("\n" + "=" * 60)
    print(f"📄 Processando aba: {aba.title}")

    df = sheets.ler_aba(aba)
    if df.empty:
        print("   (aba vazia)")
        return 0, 0

    criados, ignorados = 0, 0
    for indice, linha in df.iterrows():
        numero_linha = indice + 2  # número da linha como aparece na planilha
        dados = sheets.linha_para_dados(linha)
        issue_pai = str(linha.get("id_pai", "")).strip()

        # --- Validações: a linha é ignorada (sem interromper o lote) se falhar
        if sheets.chave_jira_valida(linha.get("id_jira")):
            print(f"⏩ Linha {numero_linha}: já possui ID {linha['id_jira']}.")
            ignorados += 1
            continue
        if not sheets.chave_jira_valida(issue_pai):
            print(f"⚠️ Linha {numero_linha}: id_pai ausente ou inválido ('{issue_pai}').")
            ignorados += 1
            continue
        if not dados["titulo"]:
            print(f"⚠️ Linha {numero_linha}: título ausente.")
            ignorados += 1
            continue

        # --- Criação e enriquecimento do caso no Jira
        issue_key = jira.criar_caso_teste(dados)
        if not issue_key:
            ignorados += 1
            continue

        print(f"✅ Criado: {dados['titulo']} → {issue_key}")
        jira.vincular_a_issue_pai(issue_key, issue_pai)
        jira.atribuir_responsavel(issue_key, account_id)
        transicionar_conforme_execucao(issue_key, dados["tipo_execucao"])

        # --- Grava o ID logo após criar: se o script parar no meio,
        #     os casos já criados não serão duplicados na próxima execução.
        df.at[indice, "id_jira"] = issue_key
        sheets.escrever_celula(aba, df, indice, "id_jira", issue_key)
        criados += 1

    print(f"\n📊 Resumo da aba '{aba.title}': ✔ {criados} criados | ⏭ {ignorados} ignorados")
    return criados, ignorados


def main():
    config.validar_configuracao()
    account_id = jira.obter_account_id()
    planilha = sheets.abrir_planilha()

    total_criados, total_ignorados = 0, 0
    for aba in sheets.abas_para_processar(planilha):
        criados, ignorados = processar_aba(aba, account_id)
        total_criados += criados
        total_ignorados += ignorados

    print("\n" + "=" * 60)
    print(f"🏁 Concluído: {total_criados} casos criados, {total_ignorados} linhas ignoradas.")


if __name__ == "__main__":
    main()
