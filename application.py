#!/usr/bin/env python3
"""
Ponto de entrada para AWS Elastic Beanstalk
Este arquivo é necessário para que o EB reconheça a aplicação Flask
"""

import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

# Importar a aplicação Flask
from app import app as application

if __name__ == "__main__":
    # Para desenvolvimento local
    application.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 