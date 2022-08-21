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
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# db connection info
with open('setting.txt', 'r') as file:
    HOST, PORT, DB_NAME = file.readline().split()
client = MongoClient(host=HOST, port=int(PORT))
db = client[DB_NAME]
trash_list = open('불용어.txt', 'r', encoding='utf8').read().splitlines()


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chats_per_sec")
async def chats_per_sec():
    docs = list(db['status'].find({}).sort('_id', -1).limit(30))
    docs.reverse()
    return list(map(lambda doc: (doc['chats_per_sec'], doc['datetime']), docs))


@app.get("/statistics/word")
async def word_list_today():
    today = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    counter = Counter()
    for channel_doc in db['word_statistics'].find({'date': today}):
        counter += Counter(channel_doc['words'])

    return dict(counter.most_common(WORD_RANK_SIZE))

@app.get("/statistics/word/{word}")
async def word_graph_weekly(word):
    result = []
    for delta in range(7, 0, -1):
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