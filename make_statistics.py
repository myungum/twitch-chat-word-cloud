import pickle
from pymongo import MongoClient
from collections import Counter
from konlpy.tag import *
import time
from tqdm import tqdm
from datetime import datetime, timedelta
import re
import os
from soynlp.word import WordExtractor
from soynlp.tokenizer import MaxScoreTokenizer

UPDATE_PERIOD = 60
RANK_SIZE = 1000

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


def make_word_frequency(today, tokenizer):
    # get difference set
    not_prepared = list(set(db['chats'].distinct('date')) - set(db['word_frequency'].distinct('date')))
    # convert str into date
    not_prepared = [datetime.strptime(date_str, '%Y-%m-%d').date() for date_str in not_prepared]
    # remove not finished date
    not_prepared = [date for date in not_prepared if date < today]
    # sort
    not_prepared.sort(reverse=True)

    if len(not_prepared) > 0:
        for date in tqdm(not_prepared):
            date_str = date.strftime('%Y-%m-%d')
            print('make word frequency:', date_str)
            counter = Counter()
            for doc in tqdm(list(db['chats'].find({'date': date_str}, {'_id': 0, 'text': 1}))):
                word_set = set()
                chat = without_hangul.sub('', doc['text']).strip()
                for word in tokenizer.tokenize(chat):
                    word_set.add(word)
                counter.update(word_set)
            
            db['word_frequency'].insert_one({
                'date': date_str,
                'data' : dict(counter.most_common(RANK_SIZE))
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

    except Exception as e:
        print('Exception :', str(e))
    finally:
        client.close()
    elapsed_time = datetime.now() - start_time
    print('elapsed time:', elapsed_time)
    if UPDATE_PERIOD > elapsed_time.seconds:
        time.sleep(UPDATE_PERIOD - elapsed_time.seconds)