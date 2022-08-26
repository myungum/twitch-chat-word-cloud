## Twitch Chat Word Cloud
##### This server can visualize chats that collected from [twitch-chat-collector](https://github.com/myungum/twitch-chat-collector/tree/master)
##### [twitch-chat-collector](https://github.com/myungum/twitch-chat-collector/tree/master)에서 수집된 채팅을 가시화해주는 서버입니다.
<img src="https://github.com/myungum/twitch-chat-word-cloud/blob/main/res/dashboard.png" width="50%">
<br>

## Okt vs Mecab
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
<br>

## 한국어 형태소 분석기와 신조어
##### 일반적인 문장을 잘 분리할 수 있음에는 분명합니다. [한국어 형태소 분석기 비교](https://iostream.tistory.com/144)
##### 하지만 사전에 없는 단어는 분리하기 어렵습니다. 다음은 실제 채팅을 Okt로 분석한 결과입니다.
```
응 어쩔티비쥬 저쩔티비쥬 안물티비쥬 안궁티비쥬  지금 화냤죠 개 킹받죠 근데 내가 사는 곳 모르쥬  쿠쿠릉삥뽕
```
```
[('응', 'Noun'), ('어쩔', 'Modifier'), ('티', 'Noun'), ('비쥬', 'Noun'), ('저', 'Determiner'), ('쩔티', 'Noun'), ('비쥬', 'Noun'), ('안물', 'Noun'), ('티', 'Noun'), ('비쥬', 'Noun'), ('안궁티', 'Noun'), ('비쥬', 'Noun'), ('지금', 'Noun'), ('화냤', 'Noun'), ('죠', 'Josa'), ('개', 'Noun'), ('킹', 'Noun'), ('받죠', 'Verb'), ('근데', 'Adverb'), ('내', 'Noun'), ('가', 'Josa'), ('사는', 'Verb'), ('곳', 'Noun'), ('모르쥬', 'Noun'), ('쿠쿠', 'Noun'), ('릉삥뽕', 'Noun')]
```
##### 띄어쓰기가 비교적 잘 지켜졌음에도 신조어를 잘 분리해 내지 못합니다.
<br>

## Dependencies
### Python
##### [fastapi](https://fastapi.tiangolo.com/)
##### [pymongo](https://pypi.org/project/pymongo/)
### Javascript
##### [anychart](https://www.anychart.com/)
