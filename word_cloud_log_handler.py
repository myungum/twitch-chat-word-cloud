import logging
from pymongo import MongoClient
from datetime import datetime


class WordCloudLogHandler(logging.Handler):
    def __init__(self, level=logging.DEBUG, conn_info: dict = None):
        super().__init__(level)
        self.client = MongoClient(host=conn_info['db_host'], port=conn_info['db_port'])
        self.collection = self.client[conn_info['db_name']]['log']
    
    def emit(self, record):
        now = datetime.now()
        print('[{}] {} {} > {} : {}'.format(now, record.levelname,
                                            record.filename, record.funcName, record.msg))

        doc = {
            'file': record.filename,  # // 파일명
            'process': record.processName,  # // 프로세스명
            'thread': record.threadName,  # // 쓰레드명
            'function': record.funcName,  # // 함수명
            'level': record.levelno,  # // 로그레벨(ex. 10)
            'levelName': record.levelname,  # // 로그레벨명(ex. DEBUG)
            'message': record.msg,  # // 오류 메시지
            'datetime': now,  # // 현재일시
        }
        self.collection.insert_one(doc)
        