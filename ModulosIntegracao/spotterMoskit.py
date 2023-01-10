import requests
import inspect
import traceback as tb

# Head requisicoes moskit
headMoskit = {'Content-Type': "application/json",
        'apikey': "a2c471ed-68d4-4693-916c-7afd42e0d943",
        "X-Moskit-Origin": "Spotter_Integracao_TI_Elysia"} # Tpken da API do Moskit

headSpotter = {
  'Content-Type': 'application/json',
  'token_exact': '35a33b30-e84b-4fcb-ae12-4dd98f569be3'}

def get_Contacts_Spotter(infos:dict, logger):
    try:
        # Verifica se existem contatos cadastrados
        if not "Contact" in infos['Lead'].keys():
            # Nao existe contatos
            print(infos['Lead'].keys())
            logger.warning("Nao existem contatos enviados pelos JSON de agendamento do spotter.")
            return []
        else:
            # Percorrendo contatos
            listContacts = infos['Lead']['Contact']
            contacts = []
            for contact in listContacts:
                name = contact['Name']
                # Verificando posicao
                if "Position" in contact.keys():
                    position = contact['Position']
                else:
                    position = '-'
                # Verificando telefone
                if "Phone" in contact.keys():
                    phone = contact['Phone']
                else:
                    phone = '-'
                # Coloca na lista
                contacts.append({'Name': name, 'Position': position, 'Phone': phone})
            return contacts
    except Exception as e:
        # Logging
        functionExec = inspect.currentframe()
        strInfo = "[module({}) -> func({}): ]".format(str(__name__),str(inspect.getframeinfo(functionExec).function)) # Coloca qual funcao ocorreu erro/info
        # CRITICAL ERROR na funcao
        error = strInfo.join(tb.format_exception(e))
        logger.critical(error)
        logger.critical("Erro critico ao buscar contatos do JSON do spotter!") 
        return []

def dados_Empresa(jsonEmpresa:dict, logger) -> dict:
    try:
        functionExec = inspect.currentframe()
        strInfo = "[module({}) -> func({}): ]".format( str(__name__),
                                                       str(inspect.getframeinfo(functionExec).function) )
        # Criando dicionario
        dictDados = {'origemEmpresa': '',
                    'preVendedor': '',
                    'origemCaptacao': '',
                    'endereco': ''}
        
        # Preenchendo informacoes
        dictDados['origemEmpresa'] = str(jsonEmpresa['Lead']['Industry']['value'])
        dictDados['preVendedor'] = " ".join([str(jsonEmpresa['Lead']['SDR']['Name']),str(jsonEmpresa['Lead']['SDR']['LastName'])])
        dictDados['origemCaptacao'] = str(jsonEmpresa['Lead']['Origem']['value'])
        dictDados['endereco'] = ", ".join([str(jsonEmpresa['Lead']['Endereco']['Endereco_Maps']),
                                            str(jsonEmpresa['Lead']['Endereco']['Logradouro']),
                                            str(jsonEmpresa['Lead']['Endereco']['Complemento'])])

        return dictDados
    except Exception as e:
        # Loggin Warning
        error = strInfo.join(tb.format_exception(e))
        logger.critical("Erro ao buscar dados da empresa: " + error)
        # Em caso de erro retorna o que foi preenchido
        return  dictDados

def formatacao_Filtros_Moskit(jsonFiltros:dict, logger) -> str:
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
    
def lista_Users_Moskit(logger) -> list:
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
        req = requests.get(url="https://api.moskitcrm.com/v2/users", headers=headMoskit, params=queryString) # 50 eh o maximo para cada requisicao

        # Pega lista de usuarios do moskit
        dic = req.json()

        # Pega quanto tem para buscar e quanto ja foi buscado na primeira requisicao
        totalToSearch = int(req.headers['X-Moskit-Listing-Total'])
        totalSearch = int(req.headers['X-Moskit-Listing-Present'])

        # Enquanto a quantidade de buscas for diferente do total para buscar, continua buscando e colocando ao dicionario
        while (totalSearch != totalToSearch and req.status_code == 200) or (stopOverflow >=100):
            # Token para proxima pasta no header
            queryString['nextPageToken'] = req.headers['X-Moskit-Listing-Next-Page-Token']

            req = requests.get(url="https://api.moskitcrm.com/v2/users", headers=headMoskit, params=queryString) 
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

def search_Id_Moskit_User(logger, jsonAgendamento, allUsers:list=[]) -> int:
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