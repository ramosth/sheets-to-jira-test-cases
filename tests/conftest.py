"""Configuração do pytest: torna a raiz do projeto importável nos testes."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
