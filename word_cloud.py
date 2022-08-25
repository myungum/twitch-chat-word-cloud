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


@app.get("/word_count/all/today",
         summary="Get today's word frequency")
async def word_count_today_all():
    today = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    counter = Counter()
    for channel_doc in db['word_statistics'].find({'date': today}):
        counter += Counter(channel_doc['words'])

    return dict(counter.most_common(WORD_RANK_SIZE))


@app.get("/word_count/specify/{word}/{period}",
         summary="Get number of word in 10 days")
async def word_count_in_10days(word: str, period: int):
    result = []
    for delta in range(period, 0, -1):
        target_day = (datetime.now() - timedelta(days=delta)).strftime('%Y-%m-%d')
        count = 0
        for channel_doc in db['word_statistics'].find({'date': target_day}, {'_id': 0, 'words.' + word: 1}):
            if word in channel_doc['words']:
                count += channel_doc['words'][word]
        result.append({
            "x": target_day,
            "y": count
        })
    return result
