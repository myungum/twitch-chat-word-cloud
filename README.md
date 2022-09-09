## Twitch Chat Word Cloud
##### This server can visualize chats that collected from [twitch-chat-collector](https://github.com/myungum/twitch-chat-collector/tree/master)
##### [twitch-chat-collector](https://github.com/myungum/twitch-chat-collector/tree/master)에서 수집된 채팅을 가시화해주는 서버입니다.
<img src="https://github.com/myungum/twitch-chat-word-cloud/blob/main/res/dashboard.png" width="50%">
<br>

[1. Okt vs Mecab](#okt-vs-mecab) <br>
[2. 한국어 형태소 분석기와 신조어](#한국어-형태소-분석기와-신조어) <br>
[3. soynlp를 이용한 신조어 분석](#soynlp를-이용한-신조어-분석) <br>
[4. 신조어 분석 성능 비교](#신조어-분석-성능-비교) <br>

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
일반적인 문장을 잘 분리할 수 있음에는 분명합니다. [한국어 형태소 분석기 비교](https://iostream.tistory.com/144)<br>
하지만 사전에 없는 단어는 분리하기 어렵습니다. 다음은 실제 채팅을 Okt로 분석한 결과입니다.<br>
```
응 어쩔티비쥬 저쩔티비쥬 안물티비쥬 안궁티비쥬  지금 화냤죠 개 킹받죠 근데 내가 사는 곳 모르쥬  쿠쿠릉삥뽕
```
```
[('응', 'Noun'), ('어쩔', 'Modifier'), ('티', 'Noun'), ('비쥬', 'Noun'), ('저', 'Determiner'), ('쩔티', 'Noun'), ('비쥬', 'Noun'), ('안물', 'Noun'), ('티', 'Noun'), ('비쥬', 'Noun'), ('안궁티', 'Noun'), ('비쥬', 'Noun'), ('지금', 'Noun'), ('화냤', 'Noun'), ('죠', 'Josa'), ('개', 'Noun'), ('킹', 'Noun'), ('받죠', 'Verb'), ('근데', 'Adverb'), ('내', 'Noun'), ('가', 'Josa'), ('사는', 'Verb'), ('곳', 'Noun'), ('모르쥬', 'Noun'), ('쿠쿠', 'Noun'), ('릉삥뽕', 'Noun')]
```
띄어쓰기가 비교적 잘 지켜졌음에도 <b>신조어를 잘 분리해 내지 못합니다.</b>
<br>
<br>

## [soynlp](https://github.com/lovit/soynlp#maxscoretokenizer)를 이용한 신조어 분석
비지도학습으로 토크나이저를 만듭니다.
```
응 어쩔티비쥬 저쩔티비쥬 안물티비쥬 안궁티비쥬  지금 화냤죠 개 킹받죠 근데 내가 사는 곳 모르쥬  쿠쿠릉삥뽕
```
```
# soynlp를 이용해 7일치 채팅을 학습한 결과
['응', '어', '쩔티비', '쥬', '저', '쩔티비', '쥬', '안물티비쥬', '안궁티비쥬', '지금', '화냤죠', '개', '킹받', '죠', '근데', '내가', '사는', '곳', '모르', '쥬', '쿠쿠릉', '삥뽕']
```
기대보다 좋지 않은 성능을 보여줍니다. 그래도 대상만 잘 맞으면 좋은 성능을 낼 것 같습니다. <b>게임 용어는 Okt보다 긍정적인 면이 있습니다.</b>
```
샨디니나브보다일리아칸레이드가먼저나올거같아요?
별수호자탈리야 웃음벨이네
```
```
# Okt
['샨디니나브', '보다', '일', '리아', '칸', '레이드', '가', '먼저', '나올거', '같아요', '?']
['별', '수호', '자', '탈', '리야', '웃음', '벨', '이네']
```
```
# soynlp를 이용해 7일치 채팅을 학습한 결과
['샨디', '니나브', '보다', '일리아칸', '레이드', '가', '먼저', '나올거', '같아요', '?']
['별수호자', '탈리야', '웃음벨이네']
```
<br>

## 신조어 분석 성능 비교
표본 데이터 : 연속된 7일간 채팅 (29,942,571개) <br>
신조어 기준 : 빈도 수 상위 100개의 단어를 찾습니다. 그 중 의미가 (주관적으로)명확하지만 국립국어원 표준국어대사전에 등장하지 않는 단어를 찾습니다.
||mecab|soynlp(전처리 X)|custom(3일치 데이터)|
|--|--|--|--|
|<b>신조어 비율</b>|8%|5%|1%|
|<b>예시</b>|롤, 딜, 겜, 호우, 탑, 플, 컷, 징끼|ㅋㅋ, ㄷㄷ, ㅠㅠ, ㄹㅇ, ㄱㅇㅇ|걍
|<b>특징</b>|한 글자 외국어가 잘 검출됩니다.|자음 신조어가 잘 검출됩니다. 트위치 이모티콘이 검출됩니다(전처리 필요)|'아니', '진짜' 등 온전하지만 자주 쓰이는 단어가 잘 검출됩니다. 신조어가 잘 검출되지 않습니다. 
<br>

## Dependencies
### Python
##### [fastapi](https://fastapi.tiangolo.com/)
##### [pymongo](https://pypi.org/project/pymongo/)
### Javascript
##### [anychart](https://www.anychart.com/)
