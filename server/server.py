import configparser
import flask
import os
import sys

from flask import request, jsonify
from flask_basicauth import BasicAuth

app = flask.Flask(__name__)
basic_auth = BasicAuth(app)
app.config["DEBUG"] = True

config_file = 'ansible.cfg'
config_file_path = os.path.join(os.path.dirname(os.getcwd()), config_file)

if not os.path.isfile(config_file_path):
    sys.exit(1)

config = configparser.ConfigParser()
config.read(config_file_path)

if 'callback_api' in config:
    app.config['BASIC_AUTH_USERNAME'] = config['callback_api']['username']
    app.config['BASIC_AUTH_PASSWORD'] = config['callback_api']['password']


@app.route('/', methods=['POST'])
@basic_auth.required
def post():
    content = request.get_json(silent=True)
    print('Post request: {}'.format(content), flush=True)
    data = {
        'message': 'Log added successfully'
    }
    return jsonify(data)


@app.errorhandler(404)
def custom_404(e):
    data = {
        'message': 'Resource not found'
    }
    return jsonify(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
