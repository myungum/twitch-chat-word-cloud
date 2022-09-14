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

UPDATE_PERIOD = 60
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
            print('make word frequency:', date_str)
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


def make_word_increase(today):
    missing_dates = get_missing_dates(today, 'word_increase')

    if len(missing_dates) > 0:
        for date in tqdm(missing_dates):
            date_str = date.strftime('%Y-%m-%d')
            min_date_str = (date - timedelta(days=7)).strftime('%Y-%m-%d')
            print('make word increase:', date_str)

            # get data for week
            docs = list(db['word_frequency'].find({
                'date': {
                    '$gte': min_date_str,
                    '$lt': date_str
                }
            }).sort('date', 1))

            # make word increase
            increase = []
            for word, count in db['word_frequency'].find_one({'date': date_str})['data'].items():
                counts = [doc['data'][word] if word in doc['data'] else 0 for doc in docs]
                if len(counts) > 0:
                    # expected value = max(average for week, yesterday's value)
                    avg = sum(counts) / len(counts)
                    expected = max(avg, counts[-1], 1)
                    increase.append((word, (count - expected) / expected))
            
            increase.sort(key=lambda x: x[1], reverse=True)
            db['word_increase'].insert_one({
                'date': date_str,
                'data': dict(increase)
            })
                

def get_tokenizer(today):
    tokenizer_file_name = os.getcwd() + '\\soynlp_tokenizer\\' + today.strftime('%Y-%m-%d')
    if not os.path.exists(tokenizer_file_name):
        print('make tokenizer')
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
        make_word_increase(start_time.date())

    except Exception as e:
        print('Exception :', str(e))
    finally:
        client.close()
    elapsed_time = datetime.now() - start_time
    print('elapsed time:', elapsed_time)
    if UPDATE_PERIOD > elapsed_time.seconds:
        time.sleep(UPDATE_PERIOD - elapsed_time.seconds)