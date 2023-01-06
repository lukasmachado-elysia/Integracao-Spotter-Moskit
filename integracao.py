import traceback as tb
import requests
import logging
import inspect
from datetime import datetime, timedelta

# Utilizando o mesmo logger da funcao main
logger = logging.getLogger("__main__") # Alterar de acordo com o nome da função main que inicia o server FLASK

# Head requisicoes moskit
head = {'Content-Type': "application/json",
        'apikey': "a2c471ed-68d4-4693-916c-7afd42e0d943",
        "X-Moskit-Origin": "Spotter_Integracao_TI_Elysia"} # Tpken da API do Moskit

def integracacao_Spotter_Moskit(dicionario:dict):
    '''
    # Integracao Spotter Moskit
    ### Autor: Lukas Silva Machado - 06/01/2023
        * 1 - FUNCIONALIDADEs: `INTEGRACAO SPOTTER-MOSKIT` - Implementado na v1.0 do programa.
                - Quando o pré-vendedor agendar uma visita devemos criar tudo do zero.
        ----------
        * 2 - FUNCIONALDADE: `REAGENDAMENTO SPOTTER-MOSKIT` - À implementar.
                - Quando o pré-vendedor alterar o horário de uma visita devemos buscar o negócio respectivo e alterar no moskit sua data. 
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
        
        # COLOCAR AQUI COMO RETORNO A REQUISICAO DE AGENDAMENTO DO JSON MOSKIT
        #
        #
        return ("Agendado com sucesso!", 200)
    except Exception as e:
        # CRITICAL ERROR na funcao
        error = strInfo.join(tb.format_exception(e))
        logger.critical(error)
        return (error, 500)

def agendamento_Moskit(informacoes:dict):
    try:
        # ---------------------------------------------------------------------
        # Ordem de criacao de cada informacao eh:
        #                         --  Negocio  --
        #                         -- Atividade --
        #                         --  Empresa  --
        #                         --  Contato  --                        
        # ---------------------------------------------------------------------
        
        
        # ---------------------------------------------------------------------
        #               Pegando informacoes iniciais para o negocio
        
        # Buscando Vendedor
        logger.info("[API MOSKIT]: Buscando vendedor nos usuarios Moskit...")
        idVendedor = search_Id_Moskit_User(informacoes, lista_Users_Moskit())
        
        # #Dados do Agendamento
        endReunion = datetime.strptime(informacoes['Agendamento']['DtFimDateTime'].replace("'",""),"%Y-%m-%dT%H:%M:%S")
        startReunion = datetime.strptime(informacoes['Agendamento']['DtInicioDateTime'].replace("'",""),"%Y-%m-%dT%H:%M:%S")
        timeReunion = timedelta.total_seconds(endReunion - startReunion) // 60 # Tempo total (Em minutos) da reuniao
        
        # Dados da Empresa
        nomeEmpresa = str(informacoes['Lead']['Company'])

        # ---------------------------------------------------------------------
        # Criando Negocio
        payload = { "createdBy": {"id": idVendedor},    # Id do vendedor responsavel 
                    "responsible": {"id": idVendedor},  # Id do vendedor responsavel
                    "name": nomeEmpresa,                # Nome da empresa 
                    "price": 1,                         # Verificar se e importante
                    "status": "OPEN",                   # Negocio aberto
                    "stage": {"id": 109019}             # Define o estagio como sendo visita agendada
                    }

        # Insere o negocio no moskit
        req = requests.post(url="https://api.moskitcrm.com/v2/deals", json=payload, headers=head)

        # Verifica se foi possivel realizar criacao
        if req.status_code != 200:          
            # Informa o erro que ocorreu
            logger.critical("[API MOSKIT]: Erro na criacao do negocio -> " + req.json())
            # Enviar e-mail informando erro ao agendar?
            #
            #
        else:  
            # Criou negocio
            codigoNegocio = req.json()['id']

            # Criando Atividade (FILTROS)
            # Buscando filtros antes de criar a atividade
            idLead = informacoes['Lead']['Id'] # Utiliza o id do Lead para buscar as informacoes
            urlFilter = 'https://api.exactspotter.com/v3/QualificationHistories?$filter=leadId eq ' + idLead

            req = requests.get(urlFilter, headers=head)
            
            # Verifica se retornou filtros corretamente corretamente
            if req.status_code != 200:
                logger.critical("[API MOSKIT]: Erro na criacao do negocio -> " + req.json())
                # Enviar e-mail informando erro ao agendar?
                #
                #
            else:
                # Retornou filtros
                # Agora so formatar os fitros para ser inserido nas notas de criacao da atividade
                filtros = formatacao_Filtros_Moskit(req.json())

                # Criando Atividade
                payLoad = {'title': "Agendamento Pré-Venda ({})".format(nomeEmpresa),
                'createdBy': {'id': idVendedor}, # Id do vendedor responsavel
                'responsible': {'id': idVendedor}, # Id do vendedor responsavel
                'doneUser': {"id": idVendedor}, # Id do vendedor responsavel
                'type': {'id': 57647}, # Tipo: Agendamento
                'duration': timeReunion, # Duracao da reuniao    
                'dueDate': datetime.today().strftime("%Y-%m-%dT%H:%M:%S.000-%X"),
                'doneDate': datetime.today().strftime("%Y-%m-%dT%H:%M:%S.000-%X"), # Define atividade como fechada
                'notes': filtros, # Nota com filtros
                'deals': [{'id': codigoNegocio}]}

                req = requests.post(url="https://api.moskitcrm.com/v2/activities", headers=head, json=payLoad)

                # Verifica se foi possivel criar atividade
                if req.status_code != 200:
                    logger.critical("[API MOSKIT]: Erro na criacao da atividade -> " + req.json())
                    # Enviar e-mail informando erro ao agendar?
                    #
                    #
                else: 
                    # Criou Atividade
                    codigoAtividade = req.json()['id']

                    # Criando um Empresa
                    # --- Dados a inserir na empresa:----
                    #          * Telefone da Empresa
                    #          * CNPJ
                    #          * ORIGEM - TIPO DE PROSPECCAO
                    #          * MERCADO 
                    #          * ESTADO
                    #          * CIDADE
                    
                    payLoad = {"createdBy": {"id": idVendedor},                                 # Id do vendedor responsavel
                                "responsible": {"id": idVendedor},                              # Id do vendedor responsavel
                                "name": nomeEmpresa,                                            # Nome da empresa
                                'phones': [{'number': "5133333333"}],                           # Telefone da empresa
                                'emails': [{'address': "empresaInventada@inventado.com.br"}],
                                'deals': [{'id': codigoNegocio}],                               # Negocio para linkar
                                'entityCustomFields': [
                                                        {'id': 'CF_POEMy6UeCJGGjmdk', 'textValue': 'Endereco completo'},
                                                        {'id': 'CF_gvGm31U0Cz55Qq45', 'textValue': 'Lukas Machado'},
                                                        {'id': 'CF_wPVm2bU2CbRR9mK6', 'textValue': 'Q NAI'},              
                                                        {'id': 'CF_Rg7MnpULCAQQBDvd', 'textValue': 'Prospecção Ativa'}
                                                        ]} 

                    req = requests.post(url="https://api.moskitcrm.com/v2/companies", json=payLoad, headers=head)

                    
                    codigoEmpresa = req.json()['id']

        # Buscando Contato 
        #
        # -- codigo aqui
        #

        return "Agendado"
    except Exception as e:
        return "Erro"
    

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

def formatacao_Filtros_Moskit(jsonFiltros:dict) -> str:
    '''
        * Realiza a formatacao do JSON de filtros do Lead para um formato legivel ao usuario na atividade do Moskit.\n
        Retorna (str)
    '''
    try:
        functionExec = inspect.currentframe()
        strInfo = "[module({}) -> func({}): ]".format( str(__name__),
                                                       str(inspect.getframeinfo(functionExec).function) )

        stages = jsonFiltros['value'] # Retorno completo
        qa = ""
        print("Size response: {}".format(len(stages)))
        # Percorrer resposta e printar QA
        for stage in stages: # Percorre estagios do lead - filtro 1, 2, 3, Qualificados...
            qa += "# Estágio Lead: {0} #\n# Score: {1} #\n".format(stage['stage'], stage['score'])
            for question in stage['questionAnswers']: # Percorre perguntas
                for answer in question['answers']: # Percorre respostas
                    qa += "{0} -> {1}\n".format(question['question'], answer['text'])
            qa += "\n"
        return qa
    except Exception as e:
        # Loggin Warning
        error = strInfo.join(tb.format_exception(e))
        logger.critical("Erro na formatacao dos filtros: " + error)
        # Em caso de erro retorna o json em formato de string mesmo
        return str(jsonFiltros)
    

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