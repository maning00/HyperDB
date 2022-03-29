#!/usr/bin/env python3

import os
import sys
from absl import app as absl_app
from absl import flags
import flask
from flask import request, jsonify

from daemon import *

FLAGS = flags.FLAGS
flags.DEFINE_string("iroha_addr", "172.29.101.125", "iroha host address.")
flags.DEFINE_integer("iroha_port", 50051, "iroha host port.")
flags.DEFINE_string("account_id", "diva@testnet.ustb.edu", "Your account ID.")

app = flask.Flask(__name__)
app.config["DEBUG"] = True
keys = Keypair('09aae8084401f5eff033ea894fc8b2b9a2abce571261e87efcbc6398d8f36166',
               '4bd49ab25faeaad1cca9dd2fe0c0b965223c932bd1273b5911dd28033266b965')
daemon = None


@app.route("/api/v1/get_all_table", methods=['GET'])
def select():
    global daemon
    return jsonify(daemon.show_all_tables())


@app.route("/api/v1/create_table", methods=['POST'])
def create_table():
    global daemon
    data = request.get_json()
    daemon.create_table(data['table_name'])
    return "Created", 201


@app.route("/api/v1/insert", methods=['POST'])
def insert():
    global daemon
    data = request.get_json()
    j = data['data']

    if daemon.insert_data(Entry(**j)) == True:
        return "OK", 201
    else:
        return "", 500


@app.route("/api/v1/get_data", methods=['POST'])
def select_data():
    global daemon
    data = request.get_json()
    table = data['table_name']
    return json.dumps(daemon.get_data(table))


@app.route("/api/v1/select_columns", methods=['POST'])
def select_columns():
    global daemon
    data = request.get_json()
    table = data['table_name']
    columns = data['columns']
    return json.dumps(daemon.select_columns(table, columns))  # need to format the data to be sent


@app.route("/api/v1/login", methods=['POST'])
def login():
    return json.dumps({"result": "OK"})


def main(argv):
    """
    Main function.
    """
    logging.set_verbosity(logging.DEBUG)
    if sys.version_info[0] < 3:
        raise Exception('Python 3 or a more recent version is required.')
    global daemon
    daemon = Daemon(FLAGS, keys)
    app.run(host='0.0.0.0')


if __name__ == '__main__':
    absl_app.run(main)
