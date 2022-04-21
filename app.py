#!/usr/bin/env python3
import uvicorn
import os
import sys, time

from fastapi import FastAPI, Request, File, UploadFile, status, HTTPException
from werkzeug.utils import secure_filename
import ipfshttpclient
from concurrent.futures import ThreadPoolExecutor
from nextcloud import NextCloud
from nextcloud.codes import ShareType

from daemon import *

ipfs_client = ipfshttpclient.connect()

app = FastAPI(debug=True)
setting = get_settings()

upload_path = os.path.abspath(os.getcwd()) + "/uploads"
if not os.path.exists(upload_path):
    os.mkdir(upload_path)

pool = ThreadPoolExecutor(max_workers=32)
    
keys = Keypair(setting.private_key, setting.public_key)
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
        time.sleep(0.1)
    j['timestamp'] = time.time()
    pool.submit(daemon.insert_data, Entry(**j))
    return {"Inserted": j['id']}


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
    setting.nextcloud_url,
    user=setting.nextcloud_user,
    password=setting.nextcloud_password,
    session_kwargs={
        'verify': False  # to disable ssl
        }) as nxc:
        nxc.upload_file(path, 'hyperdb/' + filename)
        res = nxc.create_share('hyperdb/' + filename, share_type=ShareType.PUBLIC_LINK)
        return {"link": res.data['url']}


@app.on_event('startup')
async def startup():
    global daemon
    daemon = Daemon(keys)