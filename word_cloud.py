from pymongo import MongoClient
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import json
import time
from threading import Thread, Lock
from collections import deque

CHATS_PER_SEC_FIND_LIMIT = 30

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# db connection info
with open('settings.json', 'r') as file:
    conn_info = dict(json.load(file))
    DB_HOST, DB_PORT, DB_NAME = conn_info['db_host'], conn_info['db_port'], conn_info['db_name']
client = MongoClient(host=DB_HOST, port=int(DB_PORT))
db = client[DB_NAME]
trash_list = open('불용어.txt', 'r', encoding='utf8').read().splitlines()

cps = deque()
cps_lock = Lock()


def cal_cps():
    last_obj_id = db['chat'].find({}).sort('_id', -1).limit(1)[0]['_id']

    while True:
        start_time = datetime.now()
        cnt = 0
        for doc in db['chat'].find({'_id': {'$gt': last_obj_id}}):
            if 'PRIVMSG' in doc['message']:
                cnt += 1
            last_obj_id = doc['_id']
            
        cps_lock.acquire()
        cps.append((cnt, datetime.now()))
        while len(cps) > CHATS_PER_SEC_FIND_LIMIT:
            cps.popleft()
        cps_lock.release()

        elapsed_time = (datetime.now() - start_time).total_seconds()
        time.sleep(max(1 - elapsed_time, 0))


th = Thread(target=cal_cps)
th.daemon = True
th.start()


@app.get("/",
         summary="index.html")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chats_per_sec",
         summary="Get number of messages per second")
async def chats_per_sec():
    cps_lock.acquire()
    result = list(cps)
    cps_lock.release()
    return result


@app.get("/word/rank/today/{rank_size}",
         summary="Get word frequency for today")
async def word_count_today_all(rank_size : int):
    today = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    doc =  db['word_rank'].find_one({'date': today})
    res = list(doc['data'].items())
    if rank_size > 0:
        res = res[:rank_size]
    return res


@app.get("/word/rank/recent/{rank_size}",
         summary="Get word frequency for the nearest date")
async def word_count_recent_all(rank_size : int):
    doc = db['word_rank'].find({}, {'data': 1}).sort('date', -1)[0]
    res = list(doc['data'].items())
    if rank_size > 0:
        res = res[:rank_size]
    return res


@app.get("/word/count/specify/{word}/{period}",
         summary="Get number of word in 10 days")
async def word_count_in_10days(word: str, period: int):
    result = []
    for delta in range(period, 0, -1):
        target_day = (datetime.now() - timedelta(days=delta)).strftime('%Y-%m-%d')
        doc = db['word_frequency'].find_one({'date': target_day}, {'_id': 0, 'data.' + word: 1})
        if doc is not None:
            count = doc['data'][word] if word in doc['data'] else 0
            result.append({
                "x": target_day,
                "y": count
            })
    return result
