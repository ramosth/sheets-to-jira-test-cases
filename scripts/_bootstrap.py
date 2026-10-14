"""
Permite executar os scripts com `python scripts/<nome>.py` a partir da raiz
do projeto: adiciona a raiz ao sys.path para que os pacotes jira_utils e
sheets_utils possam ser importados.
"""

import os
import sys

RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ_PROJETO not in sys.path:
    sys.path.insert(0, RAIZ_PROJETO)
