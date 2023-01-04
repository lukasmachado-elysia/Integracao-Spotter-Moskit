import traceback as tb
import requests
import logging

# Utilizando o mesmo logger da funcao main
logger = logging.getLogger("__main__")

def agendamentoMoskit(dicionario:dict):
    try:
        # Logging
        logger.info("JSON: " + str(dicionario))

        # ---------------------------------------------------------------------
        # Para iniciar devemos definir que informacoes devem ir para o moskit
        # Sao elas:
        #                           Contato Principal
        #                               Vendedor 
        #                               Empresa
        #                       Filtros (Isso eh a atividade)
        # ---------------------------------------------------------------------

        # Buscando Vendedor
        #
        # -- codigo aqui
        #

        # Buscando Empresa ou criando uma caso nao exista
        #
        # -- codigo aqui
        #

        # Buscando Contato ou criando um caso nao exista
        #
        # -- codigo aqui
        #

        # Buscando Perguntas e respostas
        #
        # -- codigo aqui
        #

        # Criando Negocio e linkando -> Atividade, Empresa, Contato
        #
        # -- codigo aqui
        #

        # Finalizando...
        #
        #
        #
        
        return dicionario, 200
    except Exception as e:
        # Algum possivel erro interno na funcao
        nameModule = "[" + str(__name__) + "] "
        error = nameModule.join(tb.format_exception(e))
        logger.critical(error)

        return error, 500