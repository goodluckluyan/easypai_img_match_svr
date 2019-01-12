#!/usr/bin/python
#encoding:utf-8
from urllib import request
from urllib import error as  urlerr
from queue import Queue
import threading
import os
import socket
import mylog

class FileDownload:
    def __init__(self,add_download_msg_queue=None, logger=None ,name='Download'):
        self.dl_queue = Queue()
        self.is_run = True
        self.add_dl_msg_queue = add_download_msg_queue
        self.logger = mylog.logger
        self.h_thread = threading.Thread(target=self.download_process)
        self.myname = name

    def exe_download(self, url, savepath):
        try:
            request.urlretrieve(url, savepath)
        except socket.timeout:
             count = 1
             while count <= 5:
                try:
                    request.urlretrieve(url, savepath)
                    break
                except socket.timeout:
                    err_info = 'Reloading for %d time' % count if count == 1 else 'Reloading for %d times' % count
                    # print(err_info)
                    self.logger.info("%s:%s"%(self.myname, err_info))
                    count += 1
             if count > 5:
                # print("downloading picture fialed!")
                self.logger.info("%s downloading file fialed,tyr more than 5 times!"%self.myname)
                return 1
        return 0

    def download_process(self):
        while self.is_run:
            node = self.dl_queue.get()
            url_ls = node[0]
            save_path_ls = node[1]
            # print("start download %s"%url)
            dl_ret_ls = []
            for url_item, save_all_path in zip(url_ls,save_path_ls):
                try:
                    dirname = os.path.dirname(save_all_path)
                    isexist = os.path.exists(dirname)
                    if not isexist:
                        os.makedirs(dirname)
                    self.logger.info("%s:start download %s" % (self.myname, url_item))
                    # filename = url_item.split('/')[-1]
                    # if savepath[-1] != os.path.sep:
                    #     savepath += os.path.sep
                    # savepath = os.path.join(savepath, filename)
                    dl_ret = self.exe_download(url_item, save_all_path)
                    dl_ret_ls.append(dl_ret)
                except urlerr.HTTPError as e:
                    dl_ret = 1
                    # print("%s download failed(%s)"%(savepath,e))
                    self.logger.info("%s download failed(%s)" % (url_item, e))
                    dl_ret_ls.append(dl_ret)

            if sum(dl_ret_ls) == 0:
                # print("%s download complete!\n"%savepath)
                self.logger.info("%s:%s download complete!" % (self.myname, url_ls))
            else:
                # print("%s download failed\n"%(savepath))
                for ret , url_item in zip(url_ls, dl_ret_ls):
                    if ret != 0:
                        self.logger.info("%s:%s download failed" % (self.myname, url_item))

            if self.add_dl_msg_queue != None:
                id = node[2]
                type = node[3]
                msg = [id, type, dl_ret_ls]
                self.add_dl_msg_queue([id, type, dl_ret_ls])
                self.logger.info("%s:add dl msg queue!(%s)" % (self.myname, msg))

            self.dl_queue.task_done()

    def add_download_task(self, url_ls, savepath_ls, id=0, type=""):
        node = [url_ls, savepath_ls, id, type]
        self.dl_queue.put(node)
        self.logger.info("%s:cur dl queue length:%d" % (self.myname, self.dl_queue.qsize()))

    def start(self):
        self.h_thread.start()

def Schedule(a,b,c):
        '''
        a:已经下载的数据块
        b:数据块的大小
        c:远程文件的大小
       '''
        per = 100.0 * a * b / c
        print("%.2f%%"%(per))
        if per > 100 :
            per = 100
            print('%s %.2f%%'%(per))

if __name__ == '__main__':
    url = 'https://files.pythonhosted.org/package/78/d8/6e58a7130d457edadb753a0ea5708e411c100c7e94e72ad4802feeef735c/pip-1.5.4.tar.gz'
    fd = FileDownload()
    fd.start()
    fd.add_download_task([url],'d:\\')