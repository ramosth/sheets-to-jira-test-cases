"""
Autenticação com o Google Sheets via OAuth 2.0.

Fluxo:
1. Na primeira execução, abre o navegador para o usuário autorizar o acesso,
   usando o arquivo auth/credentials.json (baixado do Google Cloud Console).
2. O token gerado é salvo em auth/token.pickle.
3. Nas execuções seguintes, o token salvo é reaproveitado e renovado
   automaticamente quando expira, sem abrir o navegador de novo.

Os dois arquivos ficam fora do controle de versão (veja o .gitignore).
"""

import os
import pickle

import gspread
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from sheets_utils.config import SCOPES

# Caminhos absolutos, calculados a partir da raiz do projeto, para que os
# scripts funcionem independente da pasta de onde forem executados.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "auth", "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "auth", "token.pickle")


def obter_credenciais():
    """
    Retorna credenciais válidas do Google, reutilizando o token salvo
    sempre que possível.

    Returns:
        google.oauth2.credentials.Credentials: credenciais prontas para uso.
    """
    creds = None

    # 1. Tenta reaproveitar o token de uma execução anterior
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # 2. Token expirado: renova sem precisar do navegador
            creds.refresh(Request())
        else:
            # 3. Sem token: inicia o fluxo de autorização no navegador
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    "Arquivo auth/credentials.json não encontrado. "
                    "Veja a seção 'Autenticação com o Google' no README."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Salva o token (novo ou renovado) para as próximas execuções
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    return creds


def obter_cliente_gspread():
    """
    Retorna um cliente gspread autenticado, usado para abrir planilhas.

    Returns:
        gspread.Client: cliente autorizado.
    """
    return gspread.authorize(obter_credenciais())
