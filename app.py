#!/usr/bin/env python3

import os
import sys
from absl import app as absl_app 
from absl import flags
import flask
from flask import request, jsonify

from daemon import *



FLAGS = flags.FLAGS
flags.DEFINE_string("iroha_addr", "127.0.0.1", "iroha host address.")
flags.DEFINE_integer("iroha_port", 50051, "iroha host port.")
flags.DEFINE_string("account_id", "admin@test", "Your account ID.")


app = flask.Flask(__name__)
keys = Keypair('f101537e319568c765b2cc89698325604991dca57b9716b58016b253506cab70', '313a07e6384776ed95447710d15e59148473ccfc052a681317a72a69f2a49910')
daemon = None

@app.route("/api/v1/select", methods=['GET'])
def select():
    global daemon
    return jsonify(daemon.show_all_tables())


@app.route("/api/v1/")

def main(argv):
    """
    Main function.
    """
    if sys.version_info[0] < 3:
        raise Exception('Python 3 or a more recent version is required.')
    global daemon
    daemon = Daemon(FLAGS, keys)
    app.run(host = '0.0.0.0')
    
    

if __name__ == '__main__':
    absl_app.run(main)