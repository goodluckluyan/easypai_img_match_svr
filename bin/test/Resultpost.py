# -*- coding:utf-8 -*-
from urllib import parse,request
import urllib
import json
import threading
import mylog
import os
import time

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

def walk_dir(train_path, filter):
    training_names = os.listdir(train_path)
    # Get all the path to the images and save them in a list
    # image_paths and the corresponding label in image_paths
    image_paths = []
    for training_name in training_names:
        ext_name = os.path.splitext(training_name)[1]
        if ext_name in filter:
            image_paths += [training_name]
    return image_paths


if __name__=='__main__':
    # dirname = ['05c89290705b',
    #         '1a5536b3565f',
    #         '21966ea8d4b4',
    #         '376efb809d66',
    #         '42faa27cf618',
    #         '6651309920a9',
    #         '6c2a9e5a1f80',
    #         '7ee28d9edaa2',
    #         '852b96431a8d',
    #         '920b4e543b76',
    #         '9883723323bb',
    #         'a532e97976ad',
    #         'b11c4520d64f',
    #         'b11c4520d64f',
    #         'b1c9bcd5ed44',
    #         'b370582f0b4a',
    #         'bbc9997555b6',
    #         'be38b4137936',
    #         'de9961f3a708',
    #         'eb14b9040287',
    #         'ed5c7b9e972f',
    #         'f1fdea2414c7',
    #         'f51b79bbe9f5',
    #         'fa0b2252e7e5',
    #         'fbae1b234445']
    dirname = ['d9acd7fe7876']
    local_root_dir = 'D:\\Project\\easypai\\test_img\\'
    i = 1
    for sub_dir_name in dirname:
        files = walk_dir(os.path.join(local_root_dir, sub_dir_name), ['.jpg'])
        match_img_ls = []
        for image_file in files:
            image_node = {"ImageURL":"http://211.159.160.241:8088/%s/%s"%(sub_dir_name,image_file) ,
                         "ImageType":0}
            match_img_ls.append(image_node)


        post_val = {
                    "MsgHead" :
                     {
                        "Version":"1.0",
                        "Invoker": "user1",
                        "ResultURL":"http://211.159.160.241:8080/simulateuser",
                        "MsgID":"12347",
                        "MsgType":"request",
                        "DateTime":"2018-12-23 12:00:00",
                        "Cmd" : "MatchImage",
                        "Token" : "60e144aced1c38cf780762922ea30bfec6c04167"
                     },
                    "TemplateID":"",
                    "TaskID":"dd19010008",
                    "MatchSessionID" :"ddlm201901000802",
                    "ImageNum":len(match_img_ls),
                    "Image":match_img_ls
                    }
        i = i + 1
        ResultSend.send_th('http://39.98.62.216:8080/easypai', post_val)
        time.sleep(60)
    print('end')