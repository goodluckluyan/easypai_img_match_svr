# -*- coding:utf-8 -*-

import os
import theading
import Resultpost
import time
import random
import hashlib

def getcurtime():
    tm = time.time()
    tm_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(tm))
    return tm_str

def send_image_match(send_url,th_name):
    task_map = {'DD19010004': 'note', 'DD19010005': 'richan', 'DD19010006': 'fute',
                'DD19010007': 'binjiang', 'DD19011708': 'ruijie'}
    task_ls = list(task_map.keys())

    r = random.randint(0, 1000)
    r_i = random.randint(0, 5)
    dt = getcurtime()
    cmd = 'MatchImage'
    passwd = 'easypai'
    ls = dt+cmd+passwd
    sha1 = hashlib.sha1(ls.encode('utf-8'))
    hashcode = sha1.hexdigest()
    msg = {
            "MsgHead": {
                        "Version": "1.0",
                        "Invoker": "user1",
                        "ResultURL": "http://211.159.160.241:8080/simulateuser",
                        "MsgID": "test%s%d"%(th_name, r)
                        "MsgType": "request",
                        "DateTime": dt,
                        "Cmd": cmd,
                        "Token": hashcode
                        },
            "TemplateID": "",
            "TaskID": task_ls[r_i],
            "MatchSessionID": "ddlm201901180%04d"%r,
            "ImageNum": 4,
            "Image": [
                        {"ImageURL":"http://211.159.160.241:8088/20190104064642.jpg", "ImageType": 0},
                        {"ImageURL":"http://211.159.160.241:8088/20190104064650.jpg", "ImageType": 0},
                        {"ImageURL":"http://211.159.160.241:8088/20190104064651.jpg", "ImageType": 1},
                        {"ImageURL":"http://211.159.160.241:8088/20190104064652.jpg", "ImageType": 1}
                     ]
          }
    Resultpost.ResultSend.send(send_url, msg)

def send_template_create():
    pass


def send_video_math():
    pass




