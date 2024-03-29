import traceback as tb
import logging
import inspect
from ModulosIntegracao.agendamento import agendamento_Moskit
from ModulosIntegracao.reagendamento import reagendamento_Moskit

# Utilizando o mesmo logger da funcao main
logger = logging.getLogger("app") # Alterar na funcao AGENDAMENTO.py e REAGENDAMENTO.py

def integracacao_Spotter_Moskit(dicionario:dict):
    '''
    # Integracao Spotter Moskit
    ### Autor: Lukas Silva Machado - 06/01/2023
        * 1 - FUNCIONALIDADEs: `INTEGRACAO SPOTTER-MOSKIT` - Implementado na v1.0 do programa.
                - Quando o pré-vendedor agendar uma visita devemos criar tudo do zero.
        ----------
        * 2 - FUNCIONALDADE: `REAGENDAMENTO SPOTTER-MOSKIT` - À implementar.
                - Quando o pré-vendedor alterar o horário de uma visita devemos buscar o negócio respectivo e alterar no moskit sua data. 
        ----------
        * 3 - FUNCIONALIDADE: `ENVIO DE FEEDBACK APÓS REUNIÃO DOS EXECUTIVOS DE VENDA` - À implementar.
                - Quando o executivo de vendas finalizar a reunião e realizar o feedback, deve ser criada uma nova atividade no mesmo negócio do lead com as novas informacoes.
    '''
    try:
        # Logging
        functionExec = inspect.currentframe()
        strInfo = "[module({}) -> func({}): ]".format(str(__name__),str(inspect.getframeinfo(functionExec).function)) # Coloca qual funcao ocorreu erro/info
        # ---------------------------------------------------------------------
        # Para iniciar devemos definir que informacoes devem ir para o moskit
        # Sao elas:
        #                           Contato Principal
        #                               Vendedor 
        #                               Empresa
        #                       Filtros (Isso eh a atividade)
        # ---------------------------------------------------------------------

        # -- Aqui verificamos se o tipo de requisicao será um AGENDAMENTO ou REAGENDAMENTO --
        tipoEvento = dicionario['Event']

        if tipoEvento == 'event.schedule':
            logger.info("[API MOSKI: AGENDAMENTO]")

            # Funcao de agendamento
            agendamento_Moskit(dicionario)

        elif tipoEvento == 'event.reschedule':
            logger.info("[API MOSKIT: REAGENDAMENTO]")

            # Funcao de reagendamento
            reagendamento_Moskit(dicionario)
            
        elif tipoEvento == 'event.leadqualified':
            logger.info("[API MOSKIT]: FEEDBACK EXECUTIVO")
            with open("../requisicaoFeedback.txt", "w") as f:
                f.write(str(dicionario))
            f.close()
        # COLOCAR AQUI COMO RETORNO A REQUISICAO DE AGENDAMENTO DO JSON MOSKIT
        #
        #
        return ("Agendado com sucesso!", 200)
    except Exception as e:
        # CRITICAL ERROR na funcao
        error = strInfo.join(tb.format_exception(e))
        logger.critical(error)
        return (error, 500)
