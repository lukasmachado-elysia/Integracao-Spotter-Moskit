from flask import Flask, jsonify, request
from integracao import agendamentoMoskit
from http.client import HTTPConnection
import logging
from sys import stdout
from os import chmod

app = Flask(__name__)

# Definindo logger
HTTPConnection.debuglevel = 1

logger = logging.getLogger(__name__)

stdOut = logging.StreamHandler(stream=stdout)
file = logging.FileHandler("teste.log")

formatter = logging.Formatter("[%(levelname)s] - - [%(asctime)s] -> [%(message)s]")
stdOut.setFormatter(formatter)
file.setFormatter(formatter)

logger.setLevel(logging.DEBUG)
file.setLevel(logging.DEBUG)

logger.addHandler(stdOut)
logger.addHandler(file)

@app.route('/integracaoSpotterMoskit', methods=['GET', 'POST'])
def main():
	try:
		if request.method == 'POST':
			# Verifica se o conteudo eh um dicionario
			content = request.json
			print(content)
			info = "Verificando se a requisicao é do tipo dicionário..."
			logger.info("%s", info)
			if type(content) == dict:
				info = "Requisição correta! Iniciando integração entre o Spotter e Moskit..."
				logger.info("%s", info)
				return agendamentoMoskit(content) # Envia para a funcao que ira lidar com o dicionario e realizar a integracao
			else:
				raise TypeError("O conteudo da requisicao nao eh um dicionario!")
		elif request.method == 'GET':
			info = "\"GET - IP: {0}  {1}\" 200".format(str(request.remote_addr),request.url_charset)
			logger.info("%s", info)
			return jsonify(message='Por enquanto nada...')
	except Exception as e:
		err = "O conteudo da requisicao nao eh um dicionario!\nTipo de dado:" + str(type(content))
		logger.critical("%s", err)
		return "Critical error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
