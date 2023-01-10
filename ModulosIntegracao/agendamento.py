import traceback as tb
import requests
import logging
import inspect
from  ModulosIntegracao.spotterMoskit import lista_Users_Moskit, dados_Empresa, formatacao_Filtros_Moskit, search_Id_Moskit_User, get_Contacts_Spotter
from datetime import datetime, timedelta

# Utilizando o mesmo logger da funcao main
logger = logging.getLogger("__main__") # Alterar de acordo com o nome da função main que inicia o server FLASK

# Head requisicoes moskit
headMoskit = {'Content-Type': "application/json",
        'apikey': "a2c471ed-68d4-4693-916c-7afd42e0d943",
        "X-Moskit-Origin": "Spotter_Integracao_TI_Elysia"} # Token da API do Moskit

headSpotter = {
  'Content-Type': 'application/json',
  'token_exact': '35a33b30-e84b-4fcb-ae12-4dd98f569be3'}

def agendamento_Moskit(informacoes:dict):
    try:
        functionExec = inspect.currentframe()
        strInfo = "[module({}) -> func({}): ]".format( str(__name__),
                                                       str(inspect.getframeinfo(functionExec).function) )
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
        idVendedor = search_Id_Moskit_User(logger, informacoes, lista_Users_Moskit(logger))
        
        # Dados do Agendamento
        endReunion = datetime.strptime(informacoes['Agendamento']['DtFimDateTime'].replace("'",""),"%Y-%m-%dT%H:%M:%S")
        startReunion = datetime.strptime(informacoes['Agendamento']['DtInicioDateTime'].replace("'",""),"%Y-%m-%dT%H:%M:%S")
        timeReunion = timedelta.total_seconds(endReunion - startReunion) // 60 # Tempo total (Em minutos) da reuniao
        nomeEmpresa = str(informacoes['Lead']['Company']).upper()   

        # Buscando dados da empresa
        logger.info("[DADOS EMPRESA]: Buscando dados da empresa no json...")
        dadosEmpresa = dados_Empresa(informacoes, logger)

        # ---------------------------------------------------------------------
        # Criando Negocio
        payload = { "createdBy": {"id": idVendedor},                    # Id do vendedor responsavel 
                    "responsible": {"id": idVendedor},                  # Id do vendedor responsavel
                    "name": "Negócio " + str(nomeEmpresa),              # Nome da empresa 
                    "price": 1,                                         # Verificar se e importante
                    "status": "OPEN",                                   # Negocio aberto
                    "stage": {"id": 109019},                            # Define o estagio como sendo visita agendada
                    'entityCustomFields':[
                                            {'id': 'CF_QJXmA5ijCJwdEm25', 'textValue': dadosEmpresa['endereco']},
                                            {'id': 'CF_dVKmQ5i1CdBeWmWR', 'textValue': dadosEmpresa['preVendedor']},
                                            {'id': 'CF_x1kq6oinCwXWrMzY', 'textValue': dadosEmpresa['origemEmpresa']},              
                                            {'id': 'CF_gvGm3Bi0Cz5oaM45', 'textValue': dadosEmpresa['origemCaptacao']}         
                                         ]}

        # Insere o negocio no moskit
        logger.info("[API MOSKIT]: Criando negócio...")
        req = requests.post(url="https://api.moskitcrm.com/v2/deals", json=payload, headers=headMoskit)

        # Verifica se foi possivel realizar criacao
        if req.status_code != 200:          
            # Informa o erro que ocorreu
            logger.critical("[API MOSKIT]: Erro na criacao do negocio -> " + str(req.json()))
            # Enviar e-mail informando erro ao agendar?

            return req.json(), req.status_code          
        else:  
            # Criou negocio
            codigoNegocio = req.json()['id']
            logger.info("[API MOSKIT]: Negócio Id: " + str(codigoNegocio))

            # Criando Atividade (FILTROS)
            # Buscando filtros antes de criar a atividade
            idLead = str(informacoes['Lead']['Id']) # Utiliza o id do Lead para buscar as informacoes
            logger.info("[API SPOTTER]: Buscando filtros do lead Id: " + idLead)
            urlFilter = 'https://api.exactspotter.com/v3/QualificationHistories?$filter=leadId eq ' + idLead
            
            req = requests.get(urlFilter, headers=headSpotter)
            
            # Verifica se retornou filtros corretamente corretamente
            if req.status_code != 200:
                logger.critical("[API MOSKIT]: Erro na busca de filtros -> " + str(req.json()))
                # Enviar e-mail informando erro ao agendar?
                
                return req.json(), req.status_code
            else:
                # Retornou filtros
                # Agora so formatar os fitros para ser inserido nas notas de criacao da atividade
                logger.info("[FILTROS SPOTTER]: Formatando filtros...")
                filtros = formatacao_Filtros_Moskit(req.json(), logger)

                # Criando Atividade
                payLoad = {'title': "Agendamento Pré-Venda ({})".format(nomeEmpresa),
                'createdBy': {'id': idVendedor}, # Id do vendedor responsavel
                'responsible': {'id': idVendedor}, # Id do vendedor responsavel
                'doneUser': {"id": idVendedor}, # Id do vendedor responsavel
                'type': {'id': 57647}, # Tipo: Agendamento
                'duration': int(timeReunion), # Duracao da reuniao    
                'dueDate': datetime.today().strftime("%Y-%m-%dT%H:%M:%S.000-%X"),
                'doneDate': datetime.today().strftime("%Y-%m-%dT%H:%M:%S.000-%X"), # Define atividade como fechada
                'notes': filtros, # Nota com filtros
                'deals': [{'id': codigoNegocio}]}

                logger.info("[API MOSKIT]: Criando atividade...")
                req = requests.post(url="https://api.moskitcrm.com/v2/activities", headers=headMoskit, json=payLoad)

                # Verifica se foi possivel criar atividade
                if req.status_code != 200:
                    logger.critical("[API MOSKIT]: Erro na criacao da atividade -> " + str(req.json()))
                    # Enviar e-mail informando erro ao agendar?
                    
                    return req.json(), req.status_code
                else: 
                    # Criou Atividade
                    codigoAtividade = req.json()['id']
                    logger.info("[API MOSKIT]: Atividade Id: " + str(codigoAtividade))

                    # Criando um Empresa
                    # --- Dados a inserir na empresa:----
                    #          * ORIGEM CAPTACAO
                    #          * MERCADO 
                    #          * ESTADO
                    #          * CIDADE
                    
                    payLoad = {"createdBy": {"id": idVendedor},                                 # Id do vendedor responsavel
                                "responsible": {"id": idVendedor},                              # Id do vendedor responsavel
                                "name": nomeEmpresa,                                            # Nome da empresa
                                'phones': [{'number': "5133333333"}],                           # Telefone da empresa
                                'emails': [{'address': "empresaInventada@inventado.com.br"}],   # Email
                                'deals': [{'id': codigoNegocio}],                               # Negocio para linkar
                                'entityCustomFields': [
                                                        {'id': 'CF_POEMy6UeCJGGjmdk', 'textValue': dadosEmpresa['endereco']},
                                                        {'id': 'CF_gvGm31U0Cz55Qq45', 'textValue': dadosEmpresa['preVendedor']},
                                                        {'id': 'CF_wPVm2bU2CbRR9mK6', 'textValue': dadosEmpresa['origemEmpresa']},              
                                                        {'id': 'CF_Rg7MnpULCAQQBDvd', 'textValue': dadosEmpresa['origemCaptacao']}
                                                      ]} 

                    logger.info("[API MOSKIT]: Criando Empresa...")
                    req = requests.post(url="https://api.moskitcrm.com/v2/companies", json=payLoad, headers=headMoskit)      
                    

                    # Verifica se criou a empresa
                    if req.status_code != 200:
                        logger.critical("[API MOSKIT]: Erro na criacao da empresa -> " + str(req.json()))
                        # Enviar e-mail informando erro ao agendar?

                        return req.json(), req.status_code
                    else:
                        # Criou empresa
                        codigoEmpresa = req.json()['id']
                        logger.info("[API MOSKIT]: Empresa Id: " + str(codigoEmpresa))

                        # Percorrer contatos e ir adicionando um por um
                        contatos = get_Contacts_Spotter(informacoes, logger)
                        
                        # Variavel para verificar se foi criado algum contato
                        contatoCriado = False

                        # Criando contato
                        for contact in contatos:
                            payLoad = {'createdBy': {'id': idVendedor}, # Id do vendedor responsavel
                                        'responsible': {'id': idVendedor}, # Id do vendedor responsavel
                                        'name': contact['Name'], # Nome do contato principal
                                        'notes': contact['Position'], # Cargo do contato
                                        'phones': [{'number': contact['Phone']}], # Telefone do contato 
                                        'emails': [{'address': "contatoEmpresaInventada@inventado.com.br"}], # E-mail do contato, se tiver
                                        'deals': [{'id': codigoNegocio}], # Id do negocio para linkar
                                        'employers': [{'company': {'id': codigoEmpresa}}]} # Id da empresa para linkar

                            req = requests.post(url="https://api.moskitcrm.com/v2/contacts", json=payLoad, headers=headMoskit)

                            # Verifica se o contato foi criado
                            if req.status_code != 200:
                                logger.critical("[API MOSKIT]: Erro na criacao do contato: {}-> {}".format,(contact['Name'], str(req.json())))                  
                                return req.json(), req.status_code
                            else:
                                # Contato criado
                                codigoContato= req.json()['id']
                                contatoCriado = True
                                logger.info("[API MOSKIT]: Contato Id: " + str(codigoContato))

                        # Apos execucao
                        if not contatoCriado:
                            logger.warning("Negocio criado com ausencia de contatos!")
                            return "Id do negocio: " + str(codigoNegocio), 200
                        else:
                            logger.info("[API MOSKIT]: Negocio criado com sucesso! - - Id do negocio no Moskit: " + str(codigoNegocio))
                            # Se nao ocorrer nenhum erro retorna o codigo do negocio e sucesso no agendamento
                            return "Id do negocio: " + str(codigoNegocio), 200
    except Exception as e:
        # Loggin CRITICAL
        error = strInfo.join(tb.format_exception(e))
        logger.critical(error)
        return error, 500