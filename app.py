from flask import Flask, jsonify, request
import os
app = Flask(__name__)

@app.route('/integracaoSpotterMoskit', methods=['GET', 'POST'])
def hello_world():
	if request.method == 'POST':
		content = request.json
		with open("/home/ubuntu/dadosAgenda.txt", "w") as f:
			f.write(str(content))
		f.close()
		return "Success", 200
	elif request.method == 'GET':
		return jsonify(message='requisicao GET...')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
