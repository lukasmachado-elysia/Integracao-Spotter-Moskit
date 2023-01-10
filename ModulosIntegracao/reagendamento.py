import traceback as tb
import requests
import logging
import inspect
from ModulosIntegracao.spotterMoskit import lista_Users_Moskit, dados_Empresa, formatacao_Filtros_Moskit
from datetime import datetime, timedelta

# Utilizando o mesmo logger da funcao main
logger = logging.getLogger("__main__") # Alterar de acordo com o nome da função main que inicia o server FLASK

# Head requisicoes moskit
headMoskit = {'Content-Type': "application/json",
        'apikey': "a2c471ed-68d4-4693-916c-7afd42e0d943",
        "X-Moskit-Origin": "Spotter_Integracao_TI_Elysia"} # Tpken da API do Moskit

headSpotter = {
  'Content-Type': 'application/json',
  'token_exact': '35a33b30-e84b-4fcb-ae12-4dd98f569be3'}

def reagendamento_Moskit(informacoes:dict):
    # Buscando Empresa 
    #
    # -- codigo aqui
    #

    # Buscando Contato 
    #
    # -- codigo aqui
    #

    # Buscando perguntas e respostas (FILTROS)
    #
    # -- codigo aqui
    #

    # Buscando Negocio e realizando update da reuniao
    #
    # -- codigo aqui
    #
    return "Reagendado"