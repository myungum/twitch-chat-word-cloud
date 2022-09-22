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

UPDATE_PERIOD = 600
MIN_COUNT = 24

trash_list = open('불용어.txt', 'r', encoding='utf8').read().splitlines()
without_hangul = re.compile('[^ ㄱ-ㅎㅏ-ㅣ가-힣+]')

# connection info
with open('setting.txt', 'r') as f:
    host, port, db_name = f.readline().split()
    chat_server_ip, chat_server_port = f.readline().split()
    oauth_token = f.readline()
    client_id, client_secret = f.readline().split()
client = None
db = None


def add_log(msg):
    now = datetime.now()
    print('[{}] {}'.format(now, msg))
    db['log'].insert_one({
        'source' : __file__,
        'msg' : msg,
        'datetime' : now
    })


def get_missing_dates(today, collection_name):
    missing_dates = list(set(db['chats'].distinct('date')) - set(db[collection_name].distinct('date')))
    # convert str into date
    missing_dates = [datetime.strptime(date_str, '%Y-%m-%d').date() for date_str in missing_dates]
    # remove not finished date
    missing_dates = [date for date in missing_dates if date < today]
    # sort
    missing_dates.sort(reverse=True)
    return missing_dates


def make_word_frequency(today, tokenizer):
    missing_dates = get_missing_dates(today, 'word_frequency')

    if len(missing_dates) > 0:
        for date in tqdm(missing_dates):
            date_str = date.strftime('%Y-%m-%d')
            add_log('make word frequency: ' +  date_str)
            counter = Counter()
            for doc in tqdm(list(db['chats'].find({'date': date_str}, {'_id': 0, 'text': 1}))):
                word_set = set()
                chat = without_hangul.sub('', doc['text']).strip()
                for word in tokenizer.tokenize(chat):
                    word_set.add(word)
                counter.update(word_set)
            
            data = []
            for word, count in counter.most_common():
                if count >= MIN_COUNT:
                    data.append((word, count))
            counter = None

            db['word_frequency'].insert_one({
                'date': date_str,
                'data' : dict(data)
            })


def make_word_rank(today):
    missing_dates = get_missing_dates(today, 'word_rank')

    if len(missing_dates) > 0:
        for date in tqdm(missing_dates):
            date_str = date.strftime('%Y-%m-%d')
            min_date_str = (date - timedelta(days=7)).strftime('%Y-%m-%d')
            add_log('make word rank: ' + date_str)

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
                weekly_counts = [doc['data'][word] if word in doc['data'] else MIN_COUNT - 1 for doc in docs]
                
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
            
            
def get_tokenizer(today):
    tokenizer_file_name = os.getcwd() + '\\soynlp_tokenizer\\' + today.strftime('%Y-%m-%d')
    if not os.path.exists(tokenizer_file_name):
        add_log('make tokenizer')
        # chats for a week
        chats = []
        for date_str in tqdm([(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)]):
            for doc in db['chats'].find({'date': date_str}):
                chat = without_hangul.sub('', doc['text']).strip()
                if len(chat) > 0:
                    chats.append(chat)
                    
        # make tokenizer
        word_extractor = WordExtractor()
        word_extractor.train(chats)
        word_score_table = word_extractor.extract()
        scores = {word:score.cohesion_forward for word, score in word_score_table.items()}
        tokenizer = MaxScoreTokenizer(scores=scores)
        
        # save tokenizer
        with open (tokenizer_file_name, 'wb') as f:
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


while True:
    try:
        # db connection
        client = MongoClient(host=host, port=int(port))
        db = client[db_name]
        start_time =  datetime.now()
        
        tokenizer = get_tokenizer(start_time.date())
        make_word_frequency(start_time.date(), tokenizer)
        make_word_rank(start_time.date())

        elapsed_time = datetime.now() - start_time
        add_log('elapsed time: ' + str(elapsed_time))

        if UPDATE_PERIOD > elapsed_time.seconds:
            time.sleep(UPDATE_PERIOD - elapsed_time.seconds)
    except Exception as e:
        add_log('Exception: ' +  str(e))
    finally:
        client.close()