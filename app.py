#!/usr/bin/env python3

import os
import sys, time
from absl import app as absl_app
from absl import flags
import flask
from flask import request, jsonify
from werkzeug.utils import secure_filename
import ipfshttpclient
from nextcloud import NextCloud
from nextcloud.codes import ShareType

from daemon import *

ipfs_client = ipfshttpclient.connect()
FLAGS = flags.FLAGS
flags.DEFINE_string("iroha_addr", "172.29.101.125", "iroha host address.")
flags.DEFINE_integer("iroha_port", 50051, "iroha host port.")
flags.DEFINE_string("account_id", "diva@testnet.ustb.edu", "Your account ID.")

NEXTCLOUD_URL = "http://10.25.127.19:8080"
NEXTCLOUD_USERNAME = "admin"
NEXTCLOUD_PASSWORD = "kizZyj-dykhow-8sixcu"

app = flask.Flask(__name__)
app.config["DEBUG"] = True
upload_path = os.path.abspath(os.getcwd()) + "/uploads"
if not os.path.exists(upload_path):
    os.mkdir(upload_path)
app.config['UPLOAD_FOLDER'] = upload_path
keys = Keypair('09aae8084401f5eff033ea894fc8b2b9a2abce571261e87efcbc6398d8f36166',
               '4bd49ab25faeaad1cca9dd2fe0c0b965223c932bd1273b5911dd28033266b965')
daemon = None
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/api/v1/get_all_table", methods=['GET'])
def select():
    return jsonify(daemon.show_all_tables())


@app.route("/api/v1/create_table", methods=['POST'])
def create_table():
    data = request.get_json()
    daemon.create_table(data['table_name'])
    return "Created", 201


@app.route("/api/v1/insert", methods=['POST'])
def insert():
    data = request.get_json()
    j = data['data']
    while daemon.is_syncing:
        time.sleep(1)
    if daemon.insert_data(Entry(**j)) == True:
        return "OK", 201
    else:
        return "", 500


@app.route("/api/v1/get_data", methods=['POST'])
def select_data():
    data = request.get_json()
    table = data['table_name']
    return json.dumps(daemon.get_data(table))


@app.route("/api/v1/select_columns", methods=['POST'])
def select_columns():
    data = request.get_json()
    table = data['table_name']
    columns = data['columns']
    return json.dumps(daemon.select_columns(table, columns))  # need to format the data to be sent


@app.route("/api/v1/login", methods=['POST'])
def login():
    return json.dumps({"result": "OK"})


@app.route("/api/v1/upload_ipfs", methods=['POST'])  # save upload file
def upload_ipfs():
    if 'file' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        resp.status_code = 400
        return resp
    file = request.files['file']
    if file.filename == '':
        resp = jsonify({'message' : 'No file selected for uploading'})
        resp.status_code = 400
        return resp
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        resp = jsonify({'hash' : ipfs_client.add(path)['Hash']})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'message' : 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'})
        resp.status_code = 400
        return resp

@app.route("/api/v1/upload_cloud", methods=['POST'])  # save upload file
def upload_cloud():
    if 'file' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        resp.status_code = 400
        return resp
    file = request.files['file']
    if file.filename == '':
        resp = jsonify({'message' : 'No file selected for uploading'})
        resp.status_code = 400
        return resp
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        with NextCloud(
        NEXTCLOUD_URL,
        user=NEXTCLOUD_USERNAME,
        password=NEXTCLOUD_PASSWORD,
        session_kwargs={
            'verify': False  # to disable ssl
            }) as nxc:

            nxc.upload_file(path, 'hyperdb/' + filename)
            res = nxc.create_share('hyperdb/' + filename, share_type=ShareType.PUBLIC_LINK)
            print(res.data)
            resp = jsonify({'link' : res.data['url']})
            resp.status_code = 201
            return resp
    else:
        resp = jsonify({'message' : 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'})
        resp.status_code = 400
        return resp


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
