import traceback as tb
import requests
import logging

# Utilizando o mesmo logger da funcao main
logger = logging.getLogger("__main__")

def agendamentoMoskit(dicionario:dict):
    try:
        # Logging
        
        return "agendamentoMoskit", 200
    except Exception as e:
        # Algum possivel erro interno na funcao
        nameModule = "[" + str(__name__) + "] "
        error = nameModule.join(tb.format_exception(e))
        return error, 500