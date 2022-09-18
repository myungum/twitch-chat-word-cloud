from collections import Counter
from pymongo import MongoClient
from konlpy.tag import Okt
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import json

FIND_CHAT_LIMIT = 5000
WORD_RANK_SIZE = 500
CHATS_PER_SEC_FIND_LIMIT = 30

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# db connection info
with open('setting.txt', 'r') as file:
    HOST, PORT, DB_NAME = file.readline().split()
client = MongoClient(host=HOST, port=int(PORT))
db = client[DB_NAME]
trash_list = open('불용어.txt', 'r', encoding='utf8').read().splitlines()


@app.get("/",
         summary="index.html")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chats_per_sec",
         summary="Get number of messages per second")
async def chats_per_sec():
    docs = list(db['status'].find({}).sort('_id', -1).limit(CHATS_PER_SEC_FIND_LIMIT))
    docs.reverse()
    return list(map(lambda doc: (doc['chats_per_sec'], doc['datetime']), docs))


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
