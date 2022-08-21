# Twitch Chat Word Cloud
##### This server can visualize chats that collected from [twitch-chat-collector](https://github.com/myungum/twitch-chat-collector/tree/master)
##### [twitch-chat-collector](https://github.com/myungum/twitch-chat-collector/tree/master)에서 수집된 채팅을 가시화해주는 서버입니다.
<img src="https://github.com/myungum/twitch-chat-word-cloud/blob/main/res/dashboard.png" width="50%">

# Okt vs Mecab
### 한국어 형태소 분석기 성능 비교
##### 대상 : 한국어 채팅 데이터 5,172,850개
##### 결과 : Okt = 808초, Mecab = 51초
##### 코드
```python
# okt
okt_start = time.time()
for doc in tqdm(docs):
    okt.nouns(doc['text'])
print(time.time() - okt_start)

# mecab
mecab_start = time.time()
for doc in tqdm(docs):
    mecab.nouns(doc['text'])
print(time.time() - mecab_start)
```

# Dependencies
### Python
##### [fastapi](https://fastapi.tiangolo.com/)
##### [pymongo](https://pypi.org/project/pymongo/)
### Javascript
##### [anychart](https://www.anychart.com/)
