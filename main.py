from collections import Counter
from pymongo import MongoClient
from konlpy.tag import Okt
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import json

FIND_CHAT_LIMIT = 5000
WORD_RANGE = 100
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# db connection info
with open('setting.txt', 'r') as file:
    HOST, PORT, DB_NAME = file.readline().split()
client = MongoClient(host=HOST, port=int(PORT))
db = client[DB_NAME]
trash_list = open('불용어.txt', 'r', encoding='utf8').read().splitlines()


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/channels")
async def channels():
    return list(db['top_channels_by_chat_count'].find({}, {'_id': 0}))


@app.get("/statistics/word/{channel}")
async def word_statistics(channel):
    # fetch data
    res = db['chats'].find({'channel': channel}, {"text": 1}).sort("_id", -1).limit(FIND_CHAT_LIMIT)
    print('word_statistics :', channel)

    # tokenization & count
    okt = Okt()
    counter = Counter()
    for doc in res:
        for token in okt.nouns(doc['text']):
            if token not in trash_list:
                counter[token] += 1

    # convert into anychart's data format
    result = []
    for word in counter.most_common(WORD_RANGE):
        result.append({'x': word[0], 'value': word[1]})
    return result
