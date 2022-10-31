import pickle
from pymongo import MongoClient
from collections import Counter
import time
from tqdm import tqdm
from datetime import datetime, timedelta
import re
import os
from soynlp.word import WordExtractor
from soynlp.tokenizer import MaxScoreTokenizer
import math
import json
import traceback
import sys

UPDATE_PERIOD = 600
MIN_COUNT = 24
TOKENIZER_DIR = os.getcwd() + '/soynlp_tokenizer'
TOKENIZER_TRAIN_RANGE = 7
TOKENIZER_TRAIN_CHAT_SIZE = 10 ** 7
AVAILABLE_DATE_RANGE = 14

trash_list = open('불용어.txt', 'r', encoding='utf8').read().splitlines()
without_hangul = re.compile('[^ ㄱ-ㅎㅏ-ㅣ가-힣+]')

# connection info
with open('settings.json', 'r') as file:
    conn_info = dict(json.load(file))
client = None
db = None


def add_log(msg):
    now = datetime.now()
    print('[{}] {}'.format(now, msg))
    # db['log'].insert_one({
    #     'source': __file__,
    #     'msg': msg,
    #     'datetime': now
    # })

def get_dates(base: datetime, to_str: bool):
    date_list = [base - timedelta(days=x+1) for x in range(AVAILABLE_DATE_RANGE)]
    if to_str:
        date_list = [date.strftime('%Y-%m-%d') for date in date_list]
    return date_list

def get_missing_dates(today: datetime, collection_name: str, to_str: bool):
    missing_dates = list(
        set(get_dates(today, to_str=True))
        - set(db[collection_name].distinct('date')))
    # convert str into date
    if not to_str:
        missing_dates = [datetime.strptime(
            date_str, '%Y-%m-%d') for date_str in missing_dates]
    # sort
    missing_dates.sort(reverse=True)
    return missing_dates


def get_chats(target_date: datetime):
    lower_bound = target_date
    upper_bound = lower_bound + timedelta(days=1)
    error = 0
    docs = list(db['chat'].find({'$and': [{
                    'datetime' : {'$gte' : lower_bound}
                },
                    {
                    'datetime' : {'$lt' : upper_bound}
                }, {
                    'message' : {'$regex' : 'PRIVMSG'}
                }]}).sort('datetime', 1))
    # remove duplicated chat
    msg_dic = dict()
    front = 0
    rear = 1
    msg_dic[docs[0]['message']] = 1
    removed = set()

    while front < len(docs):
        # push
        while rear < len(docs) and (docs[rear]['datetime'] - docs[front]['datetime']).total_seconds() < 10:
            if docs[rear]['message'] in msg_dic:
                if msg_dic[docs[rear]['message']] > 0:
                    error += 1
                    removed.add(docs[rear]['_id'])
                msg_dic[docs[rear]['message']] += 1
            else:
                msg_dic[docs[rear]['message']] = 1
            rear += 1
        
        if rear >= len(docs):
            break

        if docs[rear]['message'] in msg_dic:
            msg_dic[docs[rear]['message']] += 1
        else:
            msg_dic[docs[rear]['message']] = 1
        rear += 1
        
        # pop
        while front < rear and (docs[rear - 1]['datetime'] - docs[front]['datetime']).total_seconds() >= 10:
            msg_dic[docs[front]['message']] -= 1
            front += 1

    chats = []
    for doc in docs:
        if doc['_id'] not in removed:
            try:
                msg = doc['message']
                chat = msg.split(':', 2)[-1]
                chat = chat.strip()
                if len(chat) > 0:
                    chats.append(chat)
            except:
                pass
    return chats


def make_word_frequency(today: datetime):
    missing_dates = get_missing_dates(today, 'word_frequency', to_str=False)

    if len(missing_dates) > 0:
        for date in tqdm(missing_dates):
            date_str = date.strftime('%Y-%m-%d')
            tokenizer = get_tokenizer(date)
            add_log('make word frequency: {}'.format(date_str))
            counter = Counter()
            for chat in get_chats(date):
                word_set = set()
                hangul = without_hangul.sub('', chat).strip()
                for word in tokenizer.tokenize(hangul):
                    word_set.add(word)
                counter.update(word_set)

            data = []
            for word, count in counter.most_common():
                if count >= MIN_COUNT:
                    data.append((word, count))
            counter = None

            db['word_frequency'].insert_one({
                'date': date_str,
                'data': dict(data)
            })


def make_word_rank(today: datetime):
    missing_dates = get_missing_dates(today, 'word_rank', to_str=False)

    if len(missing_dates) > 0:
        for date in tqdm(missing_dates):
            date_str = date.strftime('%Y-%m-%d')
            min_date_str = (date - timedelta(days=7)).strftime('%Y-%m-%d')
            add_log('make word rank: {}'.format(date_str))

            # get data for week
            docs = list(db['word_frequency'].find({
                'date': {
                    '$gte': min_date_str,
                    '$lt': date_str
                }
            }).sort('date', 1))

            # make word rank
            rank = []
            for word, count in db['word_frequency'].find_one({'date': date_str})['data'].items():
                weekly_counts = [doc['data'][word]
                                 if word in doc['data'] else MIN_COUNT - 1 for doc in docs]

                # expected value = max(average for week, yesterday's value)
                avg = sum(weekly_counts) / len(weekly_counts)
                expected = max(avg, weekly_counts[0])
                increase = (count - expected) / expected
                if increase > 0:
                    score = int(increase * math.log2(count))
                    rank.append((word, (score, count, increase)))

            rank.sort(key=lambda x: x[1][0], reverse=True)
            db['word_rank'].insert_one({
                'date': date_str,
                'data': dict(rank)
            })


def get_tokenizer(target_date: datetime):
    if not os.path.exists(TOKENIZER_DIR):
        os.mkdir(TOKENIZER_DIR)

    tokenizer_file_name = TOKENIZER_DIR + \
        '/' + target_date.strftime('%Y-%m-%d')

    if not os.path.exists(tokenizer_file_name):
        add_log('make tokenizer : {}'.format(tokenizer_file_name))

        # make tokenizer
        chats = get_chats(target_date)
        word_extractor = WordExtractor()
        word_extractor.train(chats)
        word_score_table = word_extractor.extract()
        scores = {word: score.cohesion_forward for word,
                  score in word_score_table.items()}
        tokenizer = MaxScoreTokenizer(scores=scores)

        # save tokenizer
        with open(tokenizer_file_name, 'wb') as f:
            pickle.dump(tokenizer, f)

        # free memory
        chats = None
        word_extractor = None
        word_score_table = None
        scores = None
        tokenizer = None

    # return tokenizer
    with open(tokenizer_file_name, 'rb') as f:
        return pickle.load(f)


try:
    # db connection
    client = MongoClient(host=conn_info['db_host'], port=conn_info['db_port'])
    db = client[conn_info['db_name']]
    start_time = datetime.now()
    today = start_time.replace(hour=0, minute=0, second=0, microsecond=0)

    make_word_frequency(today)
    make_word_rank(today)

    elapsed_time = (datetime.now() - start_time).total_seconds()
    add_log('elapsed time: {}'.format(str(elapsed_time)))
    time.sleep(max(UPDATE_PERIOD - elapsed_time, 0))
except:
    traceback.print_exc(file=sys.stderr)
finally:
    client.close()
