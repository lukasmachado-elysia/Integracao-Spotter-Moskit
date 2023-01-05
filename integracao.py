import traceback as tb
import requests
import logging
import inspect 

# Utilizando o mesmo logger da funcao main
logger = logging.getLogger("__main__")

# Head requisicoes moskit
head = {'Content-Type': "application/json",
        'apikey': "a2c471ed-68d4-4693-916c-7afd42e0d943"}

def agendamentoMoskit(dicionario:dict):
    try:
        # Logging
        #logger.info("JSON: " + str(dicionario))
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

        # Buscando Vendedor
        #
        # -- codigo aqui
        logger.info("[API MOSKIT]: Buscando vendedor nos usuarios Moskit...")
        idVendedor = search_Id_Moskit_User(dicionario, lista_Users_Moskit())
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
        
        # COLOCAR AQUI COMO RETORNO A REQUISICAO DE AGENDAMENTO DO JSON MOSKIT
        #
        #
        return ("Agendado com sucesso!", 200)
    except Exception as e:
        # CRITICAL ERROR na funcao
        error = strInfo.join(tb.format_exception(e))
        logger.critical(error)
        return (error, 500)

def lista_Users_Moskit() -> list:
    '''
        Realiza requisicoes na API do MOSKIT buscando todos os usuarios ativos e inativos.\n
        Retorna *(list)* dos usuarios.
    '''
    try:
        # Pega em qual modulo e funcao esta o fluxo
        functionExec = inspect.currentframe()
        strInfo = "[module({}) -> func({}): ]".format( str(__name__),
                                                       str(inspect.getframeinfo(functionExec).function) ) 
        # Pesquisa todos os usuarios no sistema moskit
        stopOverflow = 0
        queryString = {'quantity': 50}
        req = requests.get(url="https://api.moskitcrm.com/v2/users", headers=head, params=queryString) # 50 eh o maximo para cada requisicao

        # Pega lista de usuarios do moskit
        dic = req.json()

        # Pega quanto tem para buscar e quanto ja foi buscado na primeira requisicao
        totalToSearch = int(req.headers['X-Moskit-Listing-Total'])
        totalSearch = int(req.headers['X-Moskit-Listing-Present'])

        # Enquanto a quantidade de buscas for diferente do total para buscar, continua buscando e colocando ao dicionario
        while (totalSearch != totalToSearch and req.status_code == 200) or (stopOverflow >=100):
            # Token para proxima pasta no header
            queryString['nextPageToken'] = req.headers['X-Moskit-Listing-Next-Page-Token']

            req = requests.get(url="https://api.moskitcrm.com/v2/users", headers=head, params=queryString) 
            stopOverflow +=1 # incrementa o stopOverflow que ira impedir laço infinito neste loop caso passe do total de 100 requisicoes
            
            # Verifica se teve retorno
            if req.status_code == 200:
                dic.extend([i for i in req.json()])
                totalSearch+= int(req.headers['X-Moskit-Listing-Present'])
            else:
                # Erro ao realizar busca de mais usuarios
                # Logging CRITICAL
                logger.critical(strInfo.join("[Detalhe da Requisicao: " + str(req.json()) + " - - Enviado usuario padrao -> 36432: TOMÁS CRESTANA ZANETTI]"))

                # EM CASO DE ERRO CRITICO OU WARNING NA BUSCA DE USUARIOS, COLOCAR O TOMÁS CRESTANA ZANETTI COMO USER PADRAO
                return [{'id': 36432, 'name': 'Tomás Crestana Zanetti'}]
        logger.info("Total de usuarios encontrados no moskit: {}".format(totalSearch))
        return dic
    except Exception as e:
        # Loggin CRITICAL
        error = strInfo.join(tb.format_exception(e))
        logger.critical(error + " [Enviado usuario padrao - 36432: TOMAS CRESTANA ZANETTI]")
        # Em caso de erro CRITICO nesta funcao iremos retornar um usuario padrao
        return [{'id': 36432, 'name': 'Tomás Crestana Zanetti'}]

def search_Id_Moskit_User(jsonAgendamento, allUsers:list=[]) -> int:
    '''
        Busca o ID respectivo do representante executivo passado no JSON do SPOTTER, no MOSKIT.\n
        Retorna (int)
    '''
    # ---->>> Estou supondo fortemente que o 'jsonAgendamento' NUNCA estara vazio... <<<---- att 05/01/2023
    try:
        # Pega em qual modulo e funcao esta o fluxo
        functionExec = inspect.currentframe()
        strInfo = "[module({}) -> func({}): ]".format( str(__name__), 
                                                       str(inspect.getframeinfo(functionExec).function) ) 
        idMoskitUser = 0
        nameSalesRep = {'pNome': str(jsonAgendamento['Appointment']['SalesRep']['Name']).lower(), 'sNome': str(jsonAgendamento['Appointment']['SalesRep']['LastName']).lower()}
        
        # Cria uma lista de usuarios ativos para verificar os vendedores
        activeUsers = []
        for users in allUsers:
            if users['active'] == True:
                activeUsers.append({'id': int(users['id']), 'name': str(users['name'])})

        # Checagem do tamanho da lista, deve ser maior que 1, caso seja igual a 1 significa que foi usuario padrao - Possivel erro 
        if len(activeUsers) > 1:

            # Verificar se o nome existe na lista
            for user in activeUsers:
                name = user['name'].lower()
                # Encontrando Nome 
                # Verificar se o pNome e o sNome estao contidos no nome da lista de ativos do moskit
                # Ex.: Lista Users -> name = 'maria joaquina fernandes carvalho'
                #      JSON Agenda - {'pNome': 'maria joaquina', 'sNome': 'fernandes carvalho'}
                # O sNome deve ser splitado para verificar separadamente se cada sobrenome esta presente no nome do usuario no moskit

                pNomeEcontrado = 0
                sNomeEcontrado = 0

                if nameSalesRep['pNome'] in name: # Se primeiro nome estiver na string 'name' entao verifica se o sobrenome
                    pNomeEcontrado +=1
                    if nameSalesRep['sNome'] in name: # Verificar se sobrenome inteiro esta na string 'name'
                        sNomeEcontrado = 2 # 2 pois encontrou o sobrenome inteiro
                        idMoskitUser = user['id'] # Retorna o Id do usuario encontrado
                        break
                    else:
                        # Splitar o nameSalesRep['sName'] e verificar se cada substring do sobrenome esta presente na string 'name'
                        subStringSobrenome = nameSalesRep['sNome'].split(" ")
                        for sub in subStringSobrenome:
                            if sub in name:
                                sNomeEcontrado += 1
        else:
            # Lista de usuarios teve erro ao buscar usuarios, utilizar o padrao
            # Logging WARNING
            logger.warning(strInfo +" [Nao existem usuarios cadatrados no moskit ou todos estao inativos no momento da consulta! - - Utilizado usuario padrao -> 36432: TOMAS CRESTANA ZANETTI]")
            return 36432 # Avisar sobre este warning em logging (e e-mail, talvez)

        # -------------------------------- CAMINHO FELIZ --------------------------------
        # Nao ocorreu erro na busca, agora eh so verificar se o usuario foi encontrado
        # Verifica se o nome foi encontrado
        # -------------------------------------------------------------------------------

        if (pNomeEcontrado + sNomeEcontrado) >= 2: # Valor sendo > 3 significa que encontrou pNome completo e pelo menos 1 sobrenome 
            # Logging e retorno
            strEncontrado = '''[OK! - - API MOSKIT -> ID:{} NOME:{} - - API SPOTTER -> NOME:{}]\n\n'''.format(user['id'],user['name']," ".join([nameSalesRep['pNome'],nameSalesRep['sNome']]))
            logger.info(strEncontrado)
            return idMoskitUser
        else:
            # Nome nao encontrado
            # Logging WARNING
            logger.warning(strInfo + " [Nome nao encontrado! - - Utilizando usuario padrao -> 36432: TOMAS CRESTANA ZANETTI]")
            return 36432 # Nao foi localizado o nome e o usuario padrao sera o {'id': 36432, 'name': 'Tomás Crestana Zanetti'} -- att 05/01/2023
    except Exception as e:
            # Loggin CRITICAL
            error = strInfo.join(tb.format_exception(e))
            logger.critical(error + " [Utilizando usuario padrao - - 36432: TOMAS CRESTANA ZANETTI]")
            return 36432 # Nao foi localizado o nome e o usuario padrao sera o {'id': 36432, 'name': 'Tomás Crestana Zanetti'} -- att 05/01/2023