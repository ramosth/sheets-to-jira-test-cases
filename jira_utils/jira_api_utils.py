"""
Funções de acesso à API REST v3 do Jira Cloud.

Concentra aqui todas as chamadas HTTP ao Jira, para que os scripts em
scripts/ fiquem enxutos e focados no fluxo (ler planilha -> criar/editar).

Documentação da API: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
"""

import requests

from jira_utils import config

# Tempo máximo de espera por resposta da API (segundos)
TIMEOUT = 30


# ============================================================================
# Montagem de payloads
# ============================================================================

def texto_adf(texto):
    """
    Converte um texto simples para o formato ADF (Atlassian Document Format),
    exigido pela API v3 em campos de texto rico (descrição, campos longos).

    Args:
        texto (str): conteúdo em texto simples.

    Returns:
        dict: documento ADF com um único parágrafo.
    """
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": texto or " "}]}
        ],
    }


def montar_descricao(objetivo, pre_condicoes, cenario):
    """
    Monta a descrição do caso de teste em ADF, no padrão:

        **Objetivo:**      <texto>
        **Pré-condição:**  <texto>
        ```gherkin
        <cenário em Dado / Quando / Então>
        ```

    O cenário vai em um bloco de código com destaque de sintaxe Gherkin,
    o que facilita a leitura e a futura automação do caso.
    """

    def titulo(texto):
        # Parágrafo em negrito, usado como rótulo de cada seção
        return {
            "type": "paragraph",
            "content": [{"type": "text", "text": texto, "marks": [{"type": "strong"}]}],
        }

    def paragrafo(texto):
        return {"type": "paragraph", "content": [{"type": "text", "text": texto or " "}]}

    return {
        "type": "doc",
        "version": 1,
        "content": [
            titulo("Objetivo:"),
            paragrafo(objetivo),
            titulo("Pré-condição:"),
            paragrafo(pre_condicoes),
            {
                "type": "codeBlock",
                "attrs": {"language": "gherkin"},
                "content": [{"type": "text", "text": cenario or " "}],
            },
        ],
    }


def separar_componentes(componentes):
    """
    Converte "Front, API" (texto da planilha) em lista de componentes do Jira.
    Aceita também uma lista já pronta.
    """
    if isinstance(componentes, (list, tuple)):
        itens = componentes
    else:
        itens = str(componentes or "").split(",")
    return [{"name": c.strip()} for c in itens if str(c).strip()]


def montar_campos_caso_teste(dados):
    """
    Monta o dicionário "fields" de um caso de teste, usado tanto na criação
    quanto na edição. Os IDs dos campos personalizados vêm do .env.

    Args:
        dados (dict): titulo, objetivo, pre_condicoes, cenario,
                      tipo_execucao, tipo_teste, componentes.

    Returns:
        dict: campos no formato esperado pela API do Jira.
    """
    campos = {
        "summary": dados["titulo"],
        "description": montar_descricao(
            dados.get("objetivo"), dados.get("pre_condicoes"), dados.get("cenario")
        ),
        "components": separar_componentes(dados.get("componentes")),
    }

    # Campos personalizados só são enviados se estiverem configurados no .env,
    # assim o script funciona mesmo em projetos que não os utilizam.
    if config.CAMPO_TIPO_EXECUCAO and dados.get("tipo_execucao"):
        campos[config.CAMPO_TIPO_EXECUCAO] = {"value": dados["tipo_execucao"]}
    if config.CAMPO_TIPO_TESTE and dados.get("tipo_teste"):
        campos[config.CAMPO_TIPO_TESTE] = {"value": dados["tipo_teste"]}
    if config.CAMPO_OBJETIVO:
        campos[config.CAMPO_OBJETIVO] = texto_adf(dados.get("objetivo"))
    if config.CAMPO_PRE_CONDICOES:
        campos[config.CAMPO_PRE_CONDICOES] = texto_adf(dados.get("pre_condicoes"))

    return campos


# ============================================================================
# Chamadas à API
# ============================================================================

def _requisicao(metodo, caminho, **kwargs):
    """
    Wrapper único para as chamadas HTTP: aplica URL base, autenticação,
    cabeçalhos e timeout em um só lugar.
    """
    return requests.request(
        metodo,
        f"{config.JIRA_URL}{caminho}",
        auth=config.AUTH,
        headers=config.HEADERS,
        timeout=TIMEOUT,
        **kwargs,
    )


def obter_account_id():
    """
    Retorna o accountId do usuário dono do token. Ele é usado para atribuir
    os casos de teste criados a quem executou o script.
    """
    resposta = _requisicao("GET", "/rest/api/3/myself")
    if resposta.status_code == 200:
        return resposta.json()["accountId"]
    print(f"⚠️ Erro ao obter accountId: {resposta.status_code} - {resposta.text}")
    return None


def criar_caso_teste(dados):
    """
    Cria um caso de teste no Jira.

    Args:
        dados (dict): campos lidos da linha da planilha.

    Returns:
        str | None: chave da issue criada (ex.: "QA-123") ou None em caso de erro.
    """
    campos = montar_campos_caso_teste(dados)
    campos["project"] = {"key": config.PROJECT_KEY}
    campos["issuetype"] = {"id": config.ISSUE_TYPE_ID}

    resposta = _requisicao("POST", "/rest/api/3/issue", json={"fields": campos})
    if resposta.status_code == 201:
        return resposta.json()["key"]

    print(f"❌ Erro ao criar '{dados['titulo']}': {resposta.status_code} - {resposta.text}")
    return None


def vincular_a_issue_pai(issue_key, issue_pai):
    """
    Cria o vínculo entre a história/requisito (issue pai) e o caso de teste,
    garantindo a rastreabilidade requisito -> teste no Jira.
    """
    payload = {
        "type": {"name": config.LINK_TYPE_NAME},
        "inwardIssue": {"key": issue_pai},
        "outwardIssue": {"key": issue_key},
    }
    resposta = _requisicao("POST", "/rest/api/3/issueLink", json=payload)
    if resposta.status_code != 201:
        print(f"⚠️ Erro ao vincular {issue_key} a {issue_pai}: {resposta.status_code} - {resposta.text}")


def atribuir_responsavel(issue_key, account_id):
    """Define o responsável (assignee) da issue."""
    if not account_id:
        return
    resposta = _requisicao(
        "PUT", f"/rest/api/3/issue/{issue_key}/assignee", json={"accountId": account_id}
    )
    if resposta.status_code != 204:
        print(f"⚠️ Erro ao atribuir responsável em {issue_key}: {resposta.status_code} - {resposta.text}")


def transicionar_status(issue_key, nome_transicao):
    """
    Move a issue no workflow pelo NOME da transição (ex.: "To write").

    A API exige o ID da transição, que muda de projeto para projeto. Por isso
    primeiro listamos as transições disponíveis e procuramos pelo nome.
    """
    caminho = f"/rest/api/3/issue/{issue_key}/transitions"
    resposta = _requisicao("GET", caminho)
    if resposta.status_code != 200:
        print(f"⚠️ Erro ao listar transições de {issue_key}: {resposta.status_code}")
        return

    transicoes = resposta.json().get("transitions", [])
    transicao_id = next(
        (t["id"] for t in transicoes if t["name"].lower() == nome_transicao.lower()), None
    )
    if not transicao_id:
        disponiveis = ", ".join(t["name"] for t in transicoes) or "nenhuma"
        print(f"⚠️ Transição '{nome_transicao}' não disponível em {issue_key} (disponíveis: {disponiveis}).")
        return

    resposta = _requisicao("POST", caminho, json={"transition": {"id": transicao_id}})
    if resposta.status_code != 204:
        print(f"⚠️ Falha na transição '{nome_transicao}' de {issue_key}: {resposta.status_code} - {resposta.text}")


def atualizar_caso_teste(issue_key, dados):
    """
    Atualiza um caso de teste existente com os dados atuais da planilha.

    Returns:
        bool: True se a atualização foi aceita pelo Jira.
    """
    campos = montar_campos_caso_teste(dados)
    resposta = _requisicao("PUT", f"/rest/api/3/issue/{issue_key}", json={"fields": campos})
    if resposta.status_code == 204:
        print(f"✅ Atualizado: {issue_key}")
        return True
    print(f"⚠️ Erro ao atualizar {issue_key}: {resposta.status_code} - {resposta.text}")
    return False


def buscar_caso_teste(issue_key):
    """
    Busca os dados atuais de um caso de teste no Jira (útil para conferência).

    Returns:
        dict | None: principais campos da issue.
    """
    resposta = _requisicao("GET", f"/rest/api/3/issue/{issue_key}")
    if resposta.status_code != 200:
        print(f"⚠️ Erro ao buscar {issue_key}: {resposta.status_code} - {resposta.text}")
        return None

    campos = resposta.json().get("fields", {})
    valor = lambda campo: (campos.get(campo) or {}).get("value") if campo else None
    return {
        "titulo": campos.get("summary"),
        "status": (campos.get("status") or {}).get("name"),
        "tipo_execucao": valor(config.CAMPO_TIPO_EXECUCAO),
        "tipo_teste": valor(config.CAMPO_TIPO_TESTE),
        "componentes": [c["name"] for c in campos.get("components", [])],
    }


def excluir_issues(issue_keys):
    """
    Exclui uma ou mais issues. Útil para limpar casos criados em testes do
    próprio script. Atenção: a exclusão é permanente.
    """
    if isinstance(issue_keys, str):
        issue_keys = [issue_keys]

    for issue_key in issue_keys:
        resposta = _requisicao("DELETE", f"/rest/api/3/issue/{issue_key}")
        if resposta.status_code == 204:
            print(f"🗑️ Excluído: {issue_key}")
        else:
            print(f"⚠️ Erro ao excluir {issue_key}: {resposta.status_code} - {resposta.text}")
