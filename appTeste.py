from flask import Flask, jsonify, request
from integracao import integracacao_Spotter_Moskit
from http.client import HTTPConnection
import logging
from sys import stdout
import os

app = Flask(__name__)

# Definindo logger
HTTPConnection.debuglevel = 0

logger = logging.getLogger(__name__)

stdOut = logging.StreamHandler(stream=stdout) # Saida do log em console
fileErrors = logging.FileHandler("errorLogs/errors.log") # Salva requisicoes com erro critico em arquivo .log
fileDebug = logging.FileHandler("infoLogs/info.log") # Salva info da exec do programa

formatter = logging.Formatter("[%(levelname)s] - - {%(module)s->%(funcName)s} - - [%(asctime)s] -> %(message)s") # Formato do logger
stdOut.setFormatter(formatter) 
fileErrors.setFormatter(formatter)
fileDebug.setFormatter(formatter)

# Definindo nivel 
logger.setLevel(logging.DEBUG)
fileErrors.setLevel(logging.CRITICAL)
fileDebug.setLevel(logging.DEBUG)

# Adicionando handlers ao logger
logger.addHandler(stdOut)
logger.addHandler(fileErrors)
logger.addHandler(fileDebug)

@app.route('/integracaoSpotterMoskit', methods=['GET', 'POST'])
def main():
    try:
        if request.method == 'POST':
            # Primeiramente precisamos verificar se a requisicao manda um json
            content = request.json
            # Logging
            info = "Requisicao recebida \"POST -- {1} -- {0} - response 200\"".format(request.remote_addr, request.url_rule) 
            logger.info("%s", info)

            if type(content) == dict:
                # Logging
                info = "OK! Iniciando integracao... \"POST -- {1} -- {0} - response 200\"".format(request.remote_addr, request.url_rule) 
                logger.info("%s", info)

                # Envia para a funcao que ira lidar com o dicionario e realizar a integracao
                return integracacao_Spotter_Moskit(content) 
            else:
                # JSON nao veio
                raise TypeError("O conteudo da requisicao nao esta correto!")
        elif request.method == 'GET':
            # Logging
            info = "\"GET - - {1} - - {0} - response 200\"".format(request.remote_addr, request.url_rule)
            logger.info("%s", info)
            return jsonify(message='Por enquanto nada...'), 200
    except Exception as e:
        # Logging
        err = "O conteudo da requisicao nao esta correto!\nTipo de dado: {2} \"GET - - {1} - - {0} - response 500\"".format(request.remote_addr, request.url_rule,str(type(content)))
        logger.critical("%s", err)
        return "Critical error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
