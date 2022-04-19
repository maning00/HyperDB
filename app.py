#!/usr/bin/env python3
import uvicorn
import os
import sys, time
from absl import app as absl_app
from absl import flags

from fastapi import FastAPI, Request, File, UploadFile, status, HTTPException
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

app = FastAPI()

upload_path = os.path.abspath(os.getcwd()) + "/uploads"
if not os.path.exists(upload_path):
    os.mkdir(upload_path)
    
keys = Keypair('09aae8084401f5eff033ea894fc8b2b9a2abce571261e87efcbc6398d8f36166',
               '4bd49ab25faeaad1cca9dd2fe0c0b965223c932bd1273b5911dd28033266b965')
daemon = None
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.get("/api/v1/get_all_table/")
async def select():
    return daemon.show_all_tables()


@app.put("/api/v1/create_table/{table_name}")
async def create_table(table_name: str):
    daemon.create_table(table_name)
    return {"Created": table_name}


@app.post("/api/v1/insert/")
async def insert(info: Request):
    j = await info.json()
    while daemon.is_syncing:
        time.sleep(1)
    j['timestamp'] = time.time()
    logging.debug("insert API catched: {}".format(j))
    if daemon.insert_data(Entry(**j)) == True:
        return {"Inserted": j['id']}
    else:
        return {"Failed": j['id']}


@app.get("/api/v1/get_data/")
async def select_data(table: str):
    return daemon.get_data(table)


@app.get("/api/v1/get_history/")
async def get_history(table: str, id: int):
    return daemon.get_history(table, id)


@app.post("/api/v1/select_columns/")
async def select_columns(request: Request):
    data = await request.json()
    table = data['table_name']
    columns = data['columns']
    return daemon.select_columns(table, columns)  # need to format the data to be sent


@app.get("/api/v1/login/")
async def login():
    return {"result": "OK"}


@app.post("/api/v1/upload_ipfs/")  # save upload file
async def upload_ipfs(file: UploadFile):
    if file.filename == '':
        raise HTTPException(status_code=400, detail="No file selected")
    if file.filename.split('.')[-1] not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")
    filename = secure_filename(file.filename)
    path = os.path.join(upload_path, filename)
    save_upload_file(file, path)
    hash = ipfs_client.add(path)['Hash']
    return {"hash": hash}

@app.post("/api/v1/upload_cloud/")  # save upload file
async def upload_cloud(file: UploadFile):
    if file.filename == '':
        raise HTTPException(status_code=400, detail="No file selected")
    if file.filename.split('.')[-1] not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")
    filename = secure_filename(file.filename)
    path = os.path.join(upload_path, filename)
    save_upload_file(file, path)
    with NextCloud(
    NEXTCLOUD_URL,
    user=NEXTCLOUD_USERNAME,
    password=NEXTCLOUD_PASSWORD,
    session_kwargs={
        'verify': False  # to disable ssl
        }) as nxc:
        nxc.upload_file(path, 'hyperdb/' + filename)
        res = nxc.create_share('hyperdb/' + filename, share_type=ShareType.PUBLIC_LINK)
        return {"link": res.data['url']}


def main(argv):
    """
    Main function.
    """
    if sys.version_info[0] < 3:
        raise Exception('Python 3 or a more recent version is required.')
    global daemon
    daemon = Daemon(FLAGS, keys)
    uvicorn.run(app, host="0.0.0.0", port=5000)


if __name__ == '__main__':
    absl_app.run(main)
