# -*- coding:utf-8 -*-
from urllib import parse,request
import urllib
import json
import threading
import mylog

class MsgResultPost:
    # def __init__(self):
    #     self.post_queue = Queue()
    #
    # def start(self):
    #     self.h_thread = threading.Thread(target=self.send)
    #     self.h_thread.start()
    #
    # def add_send_msg(self,item):
    #     self.post_queue.put(item)

    def send(self, url, result_json):
        try:
            if url is None :
                return 1
            result_txt = json.dumps(result_json).encode(encoding='utf-8')
            mylog.logger.info(result_txt)
            header_dict = {'User-Agent': 'Mozilla/5.0', "Content-Type": "application/json"}

            req = request.Request(url=url, data=result_txt, headers=header_dict)
            res = request.urlopen(req)
            res = res.read()
            mylog.logger.info(res.decode(encoding='utf-8'))
            return 0
        except urllib.error.URLError as e:
            mylog.logger.info("%s %s"%(url,e))
            return 1

    def send_th(self,url, result_json):
        th = threading.Timer(1, ResultSend.send, (url, result_json,))
        th.start()
        mylog.logger.info('cur thread count :%s'%threading.active_count())

ResultSend = MsgResultPost()

if __name__=='__main__':
    d = {"MsgID": "c54977e866", "MsgType": "result", "ResultName": "DeleteTemplate",
         "Result": {"Status": "DeleteTemplateDone ", "Desc": ""}, "MatchSessionID": "",
         "TaskID": "wd18120003", "Version": 1, "DateTime": "2018-12-24 03:03:02"}

    ResultSend.send_th('http://127.0.0.1:8080/simulateuser', d)
    print('end')