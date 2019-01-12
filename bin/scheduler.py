# -*- coding:utf-8 -*-

import time
import sched
from threading import Timer
import threading
import Resultpost
import random
import copy

class Scheduler:
    '''此类实现了定时发送结果消息的功能'''

    def __init__(self):
        self.schedule = sched.scheduler( time.time,time.sleep)
        self.job_map = {}
        self.isstop = False
        self.th = threading.Thread(target=self.run)
        self.lock = threading.Lock()
        self.run = False


    def func(self):
        #print("now excuted func is %s %d"%(string1, time.time()))
        self.lock.acquire()
        keys = list(self.job_map.keys())
        if len(keys) > 0:
            for key in keys:
                if key < time.time():
                    Timer(1,  self.SendResultMsg, (self.job_map[key],)).start()
                    del self.job_map[key]
        self.lock.release()

        if not self.isstop:
            self.schedule.enter(1, 0, self.func)

    def SendResultMsg(self, msg):
        Resultpost.ResultSend.send(msg[0], msg[1])

    def AddTimerTask(self, delaytime, msg):
        self.lock.acquire()
        totime = int(time.time())+delaytime
        self.job_map[totime] = copy.deepcopy(msg)
        self.lock.release()

    def run(self):
        self.schedule.enter(1, 0, self.func)
        self.schedule.run()

    def start(self):
        if not self.run:
            self.th.start()
            self.run = True

    def stop(self):
        self.isstop = True

timer_task = Scheduler()

def add_time_task_process(name):
    r = random.Random()
    while True:
        rint = r.randint(1,5)
        int(time.time())+rint
        m = {'result':0 ,'desc':'task complete'}
        timer_task.AddTimerTask(rint, ['http://127.0.0.1:8080/simulateuser', m])
        print('add task %d'%rint)
        time.sleep(r.randint(1,10))


if __name__ == '__main__':
    timer_task.start()
    h1 = threading.Thread(target=add_time_task_process, args=("h1",))
    h2 = threading.Thread(target=add_time_task_process, args=("h2",))
    h3 = threading.Thread(target=add_time_task_process, args=("h3",))
    h1.start()
    h2.start()
    h3.start()

    #time.sleep(11)
    #print("end")
    #s.stop()