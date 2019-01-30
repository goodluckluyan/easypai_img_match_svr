# -*- coding:utf-8 -*-
import hashlib
import json
import queue
import threading
import traceback
import io
import DatabaseOpt
import DownFile
import time
import mylog
import os
import FetchImage
from PIL import Image
from Config import cfg
from Resultpost import ResultSend
import MatchImage
import VideoCompare

class Msg:
    def __init__(self, loger=None):
        self.msg_queue = queue.Queue(100)     # 外部消息队列
        self.dl_msg_queue = queue.Queue(100)  # 下载结果消息队列
        self.loger = mylog.logger
        self.request_head = {}
        self.response_desc = {}
        self.h_thread = threading.Thread(target=self.process)
        self.h_dl_thread = threading.Thread(target=self.process_dl_msg)
        self.dl_queue_lock = threading.Lock()
        self.response_desc[0] = 'success add job queue'
        self.response_desc[1] = 'syntax error'
        self.response_desc[2] = 'no enough permission '
        self.response_desc[3] = 'token error'
        self.response_desc[4] = 'this task not exist'
        self.response_desc[5] = 'this user not exist '
        self.response_desc[6] = 'program inner error '
        self.response_desc[7] = 'template already exist'
        self.response_desc[8] = 'template not exist'
        self.response_desc[9] = 'match session already exist'
        self.match_thread = {}
        self.match_v_thread = {}
        DatabaseOpt.db.cnn_db()

        # 启动下载线程
        self.dl_thread = {}
        self.dl_thread_index = 0
        for i in range(5):
            self.dl_thread[i] = DownFile.FileDownload(self.add_dl_msg_queue, loger, "Download_%d"%i)
            self.dl_thread[i].start()

        # 启动图像匹配线程
        self.match_thread_index = 0
        for i in range(5):
            self.match_thread[i] = MatchImage.MatchImage(cfg.Image_Srv_Dir, cfg.Match_Image_Base_URL ,
                                                         "Matchimage_%d"%i)
            self.match_thread[i].start()

         # 启动视频匹配线程
        self.match_v_thread_index = 0
        for i in range(3):
            self.match_v_thread[i] = VideoCompare.VideoCompare(cfg.Image_Srv_Dir, cfg.Match_Image_Base_URL ,
                                                               "MatchVideo_%d"%i)
            self.match_v_thread[i].start()

    def start(self):
        self.h_thread.start()
        self.h_dl_thread.start()

        # 初始化时，对未完成的任务加入任务队列
        self.load_uncomplate_match()
        self.load_uncomplate_template_create()

    def process_dl_msg(self):

        while True:
            dl_rst = self.dl_msg_queue.get()  # [id,下载type,下载dl_ret 0成功 -1：失败]
            try:
                id = dl_rst[0]
                dl_type = dl_rst[1]
                dl_rst_flag_ls = dl_rst[2]
                self.loger.info("process downlaod done meg :%s" % dl_rst)
                if dl_type == 'CreateTemplate':
                    resultaddr = self.request_head[id]['ResultURL']
                    save_full_path = self.request_head[id]['TemplatePath']
                    taskid = self.request_head[id]['TaskID']
                    template_type = self.request_head[id]['TemplateType']
                    if  dl_rst_flag_ls[0] == 0:
                        ret = self.generate_template_feature(save_full_path, taskid, template_type)
                        result_json = self.gen_create_template_result_msg(id, ret)
                    else:
                        result_json = self.gen_create_template_result_msg(id, dl_rst_flag_ls[0])
                    ResultSend.send_th(resultaddr, result_json)

                elif dl_type == "MatchImage":
                    resultaddr = self.request_head[id]['ResultURL']
                    if sum(dl_rst_flag_ls) != 0: # 每个下载都是成功的话dl_rst_flag_ls为0
                        result_json = self.gen_match_image_err_result_msg(id, 6) # 6 为下载失败
                        ResultSend.send_th(resultaddr, result_json)
                    else:
                        # 下载成功则插入数据库
                        sql = self.request_head[id]['Sql']
                        row = []
                        DatabaseOpt.db.exesql(sql, row)

                        # 执行图像匹配
                        if cfg.MatchImageSynProcess == 1:
                            test_result_json = self.gen_match_image_result_msg(id)
                            ResultSend.send_th(resultaddr, test_result_json)
                        else:
                            # taskid, msi, match_img_path, template_path, t_width, t_height, result_commit_url
                            taskid = self.request_head[id]['TaskID']
                            matchid = self.request_head[id]['MatchSessionID']
                            match_img_path = self.request_head[id]['SavePath']
                            template_img_path = os.path.join(cfg.DownloadDir, taskid)
                            t_width = cfg.DstImage_W
                            t_height = cfg.DstImage_H
                            self.match_thread[self.match_thread_index].add_match_image_task(taskid, matchid, match_img_path,
                                                                                            template_img_path, t_width,
                                                                                            t_height, resultaddr)
                            self.match_thread_index = (self.match_thread_index + 1) % len(self.match_thread)

                elif dl_type == "MatchVideo":
                    resultaddr = self.request_head[id]['ResultURL']
                    if dl_rst_flag_ls[0] == 0:  # 下载正常则插入数据库
                        sql = self.request_head[id]['Sql']
                        row = []
                        DatabaseOpt.db.exesql(sql, row)

                        taskid = self.request_head[id]['TaskID']
                        matchid = self.request_head[id]['MatchSessionID']
                        match_video_path = self.request_head[id]['SavePath']
                        template_img_path = os.path.join(cfg.DownloadDir, taskid)
                        t_width = cfg.DstImage_W
                        t_height = cfg.DstImage_H
                        self.match_v_thread[self.match_v_thread_index].add_video_compare_task(taskid, matchid, match_video_path,
                                                                                              template_img_path, t_width,
                                                                                              t_height, resultaddr)
                        self.match_v_thread_index = (self.match_v_thread_index + 1) % len(self.match_v_thread)
                        #result_json = self.gen_match_video_result_msg(id, dl_rst_flag_ls[0])
                    #videofilename = self.request_head[id]['VideoFileName']
                    #result_json = self.gen_match_video_test_result_msg(id, 7, videofilename)
                    #ResultSend.send_th(resultaddr, result_json)


                self.dl_msg_queue.task_done()
                del self.request_head[id]
                self.loger.info("process dl msg complete ,dl msg queue size:%d"%self.dl_msg_queue.qsize())

            except Exception as e:
                fp = io.StringIO()
                traceback.print_exc(file=fp)
                message = fp.getvalue()
                self.loger.info(message)

    def add_task_queue(self, item):
        '''加入消息队列'''
        self.msg_queue.put(item)

    def add_dl_msg_queue(self, item):
        '''加入下载完成对列'''
        self.dl_msg_queue.put(item)
        self.loger.info("cur dl msg queue size:%d" % self.dl_msg_queue.qsize())

    def process(self):
        while True:
            try:
                encode = self.msg_queue.get()
                cmdword = encode["MsgHead"]["Cmd"]
                if cmdword == "CreateTemplate":
                    self.loger.info("process msg (CreateTempate):%s" % encode)
                    self.process_create_template_msg(encode)
                elif cmdword == "DeleteTemplate":
                    self.loger.info("process msg (DeletetTemplate):%s" % encode)
                    self.process_del_template_msg(encode)
                elif cmdword == "MatchImage":
                    self.loger.info("process msg (MatchImage):%s" % encode)
                    self.process_match_image_msg(encode)
                elif cmdword == "MatchVideo":
                    self.loger.info("process msg (MatchVideo):%s" % encode)
                    self.process_match_video_msg(encode)

                self.msg_queue.task_done()
                self.loger.info("task process complete what befor download !")
                self.loger.info("task:%s" % encode)
            except Exception as e:
                fp = io.StringIO()
                traceback.print_exc(file=fp)
                message = fp.getvalue()
                self.loger.info(message)

    def process_create_template_msg(self, encode):
        '''处理创建模板消息'''
        if encode["MsgHead"]["Cmd"] != "CreateTemplate":
            self.loger.info("Msg {} can't processed process_create_template_msg!".format(encode))
            return -1
        dl_url = encode['TemplateURL']
        task_id = encode['TaskID']
        template_id = encode['TemplateID']
        tm_str = self.get_time_str()
        expand_name = dl_url.split('.')[-1]
        video_all_path = os.path.join(cfg.DownloadDir,
                                      task_id+os.path.sep+template_id+"."+expand_name)
        sql = "insert into Template(TaskID,TemplateID,TemplateName,TemplateURL,DownLoadFilePath,CreateDataTime," \
              "ResultURL,TemplateType) " \
              "values('{}','{}','{}','{}','{}','{}','{}','{}')".format(encode['TaskID'], template_id, encode['TemplateName'],
              dl_url, video_all_path, tm_str, encode['MsgHead']['ResultURL'], encode['TemplateType'])
        row = []
        DatabaseOpt.db.exesql(sql, row)

        # 添加下载任务
        self.request_head[task_id] = encode['MsgHead']
        self.request_head[task_id]['TaskID'] = task_id
        self.request_head[task_id]['TemplatePath'] = video_all_path
        if 'TemplateType' in encode.keys():
            self.request_head[task_id]['TemplateType'] = encode['TemplateType']
        else:
            self.request_head[task_id]['TemplateType'] = 'Video'

        self.dl_thread[self.dl_thread_index].add_download_task([dl_url], [video_all_path],
                                                               task_id, "CreateTemplate")
        self.dl_thread_index = (self.dl_thread_index+1) % len(self.dl_thread)

    def process_del_template_msg(self, encode):
        '''处理删除模板消息'''
        if encode["MsgHead"]["Cmd"] != "DeleteTemplate":
            self.loger.info("Msg {} can't processed process_del_template_msg!".format(encode))
            return -1
        id = encode["TaskID"]
        sql = "delete from  Template where TaskID='{}'".format(id)
        row = []
        ret = DatabaseOpt.db.exesql(sql, row)

        # 数据库的操作结果临时作为结果返回
        resultaddr = encode['MsgHead']['ResultURL']
        msg_id = encode['MsgHead']['MsgID']
        result_json = self.gen_del_template_result_msg(msg_id, id, ret)
        ResultSend.send_th(resultaddr, result_json)

    def process_match_image_msg(self, encode):
        try:
            '''处理匹配图片消息'''
            if encode["MsgHead"]["Cmd"] != "MatchImage":
                self.loger.info("Msg {} can't processed process_mathc_image_msg!".format(encode))
                return -1
            id = encode["MatchSessionID"]
            taskid = encode["TaskID"]
            phone = ''
            if 'Phone' in encode.keys():
                phone = encode['Phone']
            image_url = encode["Image"]
            image_num = encode["ImageNum"]
            result_url = encode['MsgHead']['ResultURL']
            match_rec_image_path = os.path.join(cfg.DownloadMatchSessionDir, id)
            if len(image_url) != image_num:
                pass

            id = encode['MatchSessionID']
            self.request_head[id] = encode['MsgHead']
            self.request_head[id]['TaskID'] = encode['TaskID']
            self.request_head[id]['MatchSessionID'] = encode['MatchSessionID']
            self.request_head[id]['SavePath'] = match_rec_image_path
            img_ls = encode["Image"]
            url_ls = []
            img_type = []
            img_filename_ls = []
            save_all_path_ls = []
            for img in img_ls:
                url = img["ImageURL"]
                filename = url.split('/')[-1]   #  获取url中图片的文件名
                # 图片类型，0：无票根 1：有票根
                if int(img["ImageType"]) == 1:  #  如果是带票根的则在文件名字加ocr
                    filename = filename.replace(".", "_ocr.")
                img_filename_ls.append(filename)
                url_ls.append(url)
                save_all_path_ls.append(os.path.join(match_rec_image_path, filename))

            sql = "insert into MatchSession(MatchSessionID,TaskID,Type,ObjNum,ObjPath,ResultURL,CreateTime,UserPhone) "\
                  "values('{}','{}','{}','{}','{}','{}','{}','{}')".format(id, taskid,  1, len(img_ls), match_rec_image_path,
                                                                      result_url, self.get_time_str(), phone)
            self.request_head[id]['Sql'] = sql

            self.request_head[id]['image_filename_ls'] = img_filename_ls
            self.loger.info("download image:%s save path %s"%(url_ls, save_all_path_ls))

            self.dl_thread[self.dl_thread_index].add_download_task(url_ls, save_all_path_ls,
                                                                   id, "MatchImage")
            self.dl_thread_index = (self.dl_thread_index+1)%len(self.dl_thread)
        except Exception as e:
            self.loger.info('except %s'%e)


    def process_match_video_msg(self, encode):
        '''处理匹配视频消息'''
        if encode["MsgHead"]["Cmd"] != "MatchVideo":
            self.loger.info("Msg {} can't processed process_match_video_msg!".format(encode))
            return -1
        id = encode["MatchSessionID"]
        taskid = encode["TaskID"]
        video_url = encode["VideoURL"]
        filename = video_url.split('/')[-1] #  获取url中视频的文件名
        result_url = encode['MsgHead']['ResultURL']
        match_rec_video_path = os.path.join(cfg.DownloadMatchSessionDir, id+os.path.sep+filename)
        sql = "insert into MatchSession(MatchSessionID,TaskID,Type,ObjPath,ResultURL,CreateTime) " \
              "values('{}','{}','{}','{}','{}','{}')".format(id, taskid,  2, match_rec_video_path,
                                                                  result_url, self.get_time_str())

        self.request_head[id] = encode['MsgHead']
        self.request_head[id]['TaskID'] = encode['TaskID']
        self.request_head[id]['MatchSessionID'] = encode['MatchSessionID']
        self.request_head[id]['SavePath'] = match_rec_video_path
        self.request_head[id]['Sql'] = sql
        self.dl_thread[self.dl_thread_index].add_download_task([video_url], [match_rec_video_path],
                                                               id, "MatchVideo")
        self.dl_thread_index = (self.dl_thread_index+1)%len(self.dl_thread)

    def generate_template_feature(self, template_full_path, taskid, template_type):
        try:
            # 更新下载完成时间
            str_tm = self.get_time_str()
            sql = 'update Template set DownloadDone=1,DownloadTime=\"%s\" where TaskID=\"%s\"' %(str_tm,
                                                                                  taskid)
            row = []
            DatabaseOpt.db.exesql(sql, row)

            if template_type == 'Video':
                # 获取视频流信息
                stream_info = {}

                frequency = cfg.GET_IMAGE_FREQUECE_FROM_VIDEO
                #FetchImage.get_vf_info(template_full_path, stream_info)
                FetchImage.fetch_image(template_full_path, frequency, cfg.DstImage_W ,cfg.DstImage_H)
                sql=''
                if len(stream_info) > 0:
                    self.loger.info("%s format info :%s" % (template_full_path,stream_info))
                    sql = 'insert into TemplateDetail(TemplateID,CreateDataTime,FeaturePath,Duration,' \
                          'FrameRate,Frequency,FeatureType,VideoWidth,VideoHeight,DstImageWidth,DstImageHeight)' \
                           ' values(\"%s\",\"%s\",\"%s\",%d,\"%s\",%.2f,\"%s\",%d,%d,%d,%d)'%(taskid, str_tm,
                           template_full_path,stream_info['duration'],stream_info['frame_rate'], float(frequency), cfg.Feature_type,
                           stream_info['width'], stream_info['height'], cfg.DstImage_W, cfg.DstImage_H)

                else:
                    self.loger.info("%s format info :%s" % (template_full_path,stream_info))
                    sql = 'insert into TemplateDetail(TemplateID,CreateDataTime,FeaturePath,Duration,' \
                          'FrameRate,Frequency,FeatureType,VideoWidth,VideoHeight,DstImageWidth,DstImageHeight)' \
                           ' values(\"%s\",\"%s\",\"%s\",%d,\"%s\",%.2f,\"%s\",%d,%d,%d,%d)'%(taskid, str_tm,
                           template_full_path,0,'0', float(frequency), cfg.Feature_type,
                           0, 0, cfg.DstImage_W, cfg.DstImage_H)
                row = []
                DatabaseOpt.db.exesql(sql, row)
            elif template_type == 'Image':
                new_img_name, img_ext_name = os.path.splitext(template_full_path)
                if 'bmp' not in img_ext_name:
                    img = Image.open(template_full_path)
                    new_img_name = new_img_name + '.bmp'
                    img.save(new_img_name)
                    self.loger.info('tranform image to bmp (%s->%s)' % (template_full_path, new_img_name))


            # 提取每个图片的特征，并保存成文件

            # 获取所有bmp图片的路径
            dirname = os.path.dirname(template_full_path)
            str_tm = self.get_time_str()
            bmp_file_ls = []
            for dirpath,dirs,filenames in os.walk(dirname):
                for file in filenames:
                    ext_name = os.path.splitext(file)[1]
                    if ext_name == '.bmp':
                        file_full_path = os.path.join(dirpath, file)
                        bmp_file_ls.append(file_full_path)

            # 对每张图进行特征提取，并保存成文件和计入数据库
            bmp_num = len(bmp_file_ls)
            bmp_process_num = 0
            for bmp_file in bmp_file_ls:
                full_name = os.path.splitext(bmp_file)[0]
                cmd = 'sudo %s -t %s -i %s' % (cfg.FeatureExtractCmd, cfg.Feature_type, bmp_file)
                self.loger.info(cmd)
                featurenum=''
                with os.popen(cmd) as p:
                    bmp_process_num += 1
                    featurenum = p.readline()[:-1]
                    feature_full_path = "%s_%s.%s"%(full_name, featurenum, cfg.Feature_type)
                    self.loger.info("%s(%s)" % (feature_full_path,featurenum))
                    if int(featurenum) > 0 and os.path.isfile(feature_full_path):
                        if template_type == 'Video':
                            filename = os.path.basename(bmp_file)
                            ordinal = filename.split('.')[0]
                            sql = 'insert into Features(uuid,ad_filename,bmp_fullFilePath,' \
                                  'fullFilePath,picture_order,quantity,bmp_quantity) values(\"%s\",\"%s\",' \
                                  '\"%s\",\"%s\",%s,%s,%d)' % (taskid, template_full_path, bmp_file, feature_full_path,
                                                                ordinal, featurenum, bmp_num)
                            row = []
                            DatabaseOpt.db.exesql(sql, row)
                        else:
                            sql = 'insert into Features(uuid,ad_filename,bmp_fullFilePath,' \
                                  'fullFilePath,picture_order,quantity,bmp_quantity) values(\"%s\",\"%s\",' \
                                  '\"%s\",\"%s\",%d,%s,%d)' % (taskid, template_full_path, bmp_file, feature_full_path,
                                                                0, featurenum, bmp_num)
                            row = []
                            DatabaseOpt.db.exesql(sql, row)

            if bmp_num > 0 and bmp_process_num > 0:
                sql = 'update Template set IsGenFeature=1 where TaskID=\"%s\"' %(taskid)
                row = []
                DatabaseOpt.db.exesql(sql, row)

            return 0
        except Exception as e:
            fp = io.StringIO()
            traceback.print_exc(file=fp)
            message = fp.getvalue()
            self.loger.info(message)

            return -1

    def verify_msg(self, msg_json):
        msg_head = msg_json["MsgHead"]
        vh = self.verify_msg_head(msg_head)
        if vh == 0:
            cmd = msg_head['Cmd']
            if cmd == "CreateTemplate":
               is_exist = self.verify_template_isexist(msg_json["TemplateID"])
               if is_exist:
                   return 7
               else:
                    return 0
            elif cmd == "DeleteTemplate":
                is_exist = self.verify_taskid_isexist(msg_json["TaskID"])
                if is_exist:
                    return 0
                else:
                    return 8
            elif cmd == "MatchImage":
                is_exist = self.verify_taskid_isexist(msg_json["TaskID"])
                if is_exist:
                    sess_exist = self.verify_match_session_id_isexist(msg_json["MatchSessionID"])
                    if sess_exist:  # 会话已经存在
                        return 9
                    else:  # 会话不存在
                        return 0
            elif cmd == "MatchVideo":
                is_exist = self.verify_taskid_isexist(msg_json["TaskID"])
                if is_exist:
                    sess_exist = self.verify_match_session_id_isexist(msg_json["MatchSessionID"])
                    if sess_exist: # 会话已经存在
                        return 9
                    else: # 会话不存在
                        return 0
                else:
                    return 8
        else:
            return vh


    def verify_msg_head(self,msg_head):
        '''token=sha1(DateTime+Cmd+调用方口令)'''
        try:
            dt = msg_head["DateTime"]
            cmd = msg_head["Cmd"]
            passwd = 'easypai'
            ls = dt+cmd+passwd
            sha1 = hashlib.sha1(ls.encode('utf-8'))
            hashcode = sha1.hexdigest()
            self.loger.info("token:%s  local token:%s"%(msg_head["Token"],hashcode))
            if hashcode == msg_head["Token"]:
                 return 0
            else:
                 return 3
        except KeyError as e:
            self.loger.info("except:%s" % e)
            return 1

    def verify_template_isexist(self, templateid):
        sql = "select * from Template where TemplateID='%s'" % templateid
        row = []
        DatabaseOpt.db.exesql(sql, row)
        if len(row) == 0:
            return False
        else:
            return True

    def verify_taskid_isexist(self, taskid):
        sql = "select * from Template where TaskID='%s'" % taskid
        row = []
        DatabaseOpt.db.exesql(sql, row)
        if len(row) == 0:
            return False
        else:
            return True

    def verify_match_session_id_isexist(self, sessionid):
            sql = "select * from MatchSession where MatchSessionID='%s'" % sessionid
            row = []
            DatabaseOpt.db.exesql(sql, row)
            if len(row) == 0:
                return False
            else:
                return True

    def gen_resp(self, msgid, cmd, validata_rst):
        '''
           0：成功加入任务队列；1：语法错误；    2：没有权限；3：Token错误；
           4：任务不存在；      5：用户不存在；  6：内部错误；7:模板已存在
           8: 模板不存在        9：匹配会话已经存在
        '''
        tm = time.time()
        info = ""
        if validata_rst in self.response_desc.keys():
            info = self.response_desc[validata_rst]
        else:
            info = "other error"
        tm_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(tm))
        response={"Version": 1, "MsgID": msgid, "MsgType": "response", "DateTime": tm_str,
                  "ResponseName": cmd, "Return": validata_rst, "Desc": info}

        response_str = json.dumps(response)
        return response_str

    def gen_create_template_result_msg(self, id, result):
        '''{"Version":1,   "MsgID":12342,    "MsgType":"result",
            "DateTime":"2018-02-26 12:00:00" ,    "TaskID"： : "dd18110001"
            "MatchSessionID" : ""    "ResultName" : "CreateTemplate",
            "Result" : {“Status”："CreateDone"}
            “Desc”:”successful”}'''

        tm_str = self.get_time_str()
        request_head = self.request_head[id]
        err_desc = ""
        if result == 0:
            err_desc = "CreateDone"
        elif result > 0:
            err_desc = "DownLoadTemplateFailed "
        elif result < 0:
            err_desc = "CreateFailed"

        result_json = {"Version": 1, "MsgID": id, "MsgType": "result",
            "DateTime": tm_str,    "TaskID": request_head["TaskID"],
            "MatchSessionID": "", 'ResultName': 'CreateTemplate',
            "Result": {'Status': result, 'Desc': err_desc}}
        return result_json

    def gen_del_template_result_msg(self, msgid, id, result):
        '''{"Version":1,   "MsgID":12342,    "MsgType":"result",
            "DateTime":"2018-02-26 12:00:00" ,    "TaskID"： : "dd18110001"
            "MatchSessionID" : ""    "ResultName" : "CreateTemplate",
            "Result" : {“Status”："CreateDone"}
            “Desc”:”successful”}'''

        rst_map = {0: "DeleteTemplateDone ", 1: "TemplateNoExist ", -1: "DeleteTemplateFailed "}
        tm_str = self.get_time_str()
        status = rst_map[result]
        result_json = {"Version": 1, "MsgID": msgid, "MsgType": "result",
            "DateTime": tm_str,    "TaskID": id,
            "MatchSessionID": "", 'ResultName': 'DeleteTemplate',
            "Result": {'Status': status, 'Desc': ''}}
        return result_json

    def gen_match_image_err_result_msg(self, id, result):
        rst_map = {6: "DownLoadImageFailed", 8: "MatchFailed"}
        tm_str = self.get_time_str()
        request_head = self.request_head[id]
        match_id = self.request_head[id]["MatchSessionID"]
        err_desc = rst_map[result]
        result_json = {"Version": 1, "MsgID": id, "MsgType": "result",
            "DateTime": tm_str,    "TaskID": request_head["TaskID"],
            "MatchSessionID" : match_id, 'ResultName': 'MatchImage',
            "Result": {'Status': result, 'Desc': err_desc}}
        return result_json

    def gen_match_image_test_result_msg(self, id, result, img_ls):
        rst_map = {6: "DownLoadImageFailed", 7: "MatchComplete", 8: "MatchFailed"}
        tm_str = self.get_time_str()
        request_head = self.request_head[id]
        match_id = self.request_head[id]["MatchSessionID"]
        err_desc = rst_map[result]
        detail = []
        for img_file in img_ls:
            item = {'image': img_file, 'status':0 , 'desc': 'MatchSuccess',
                    'url': 'http://www.test.com/test.jpg'}
            detail.append(item)
        result_json = {"Version": 1, "MsgID": id, "MsgType": "result",
            "DateTime": tm_str,    "TaskID": request_head["TaskID"],
            "MatchSessionID" : match_id, 'ResultName': 'MatchImage',
            "Result": {'Status': result, 'Desc': err_desc, 'Detail': detail}}
        return result_json


    def gen_match_image_result_msg(self, id):
        rst_map = {6: "DownLoadImageFailed", 7: "MatchComplete", 8: "MatchFailed"}
        tm_str = self.get_time_str()
        match_id = self.request_head[id]["MatchSessionID"]
        match_img_path = self.request_head[id]['savepath']
        taskid = self.request_head[id]['TaskID']
        template_img_path = os.path.join(cfg.DownloadDir, taskid)
        cmd = 'sudo /root/easypai/ImageCompare/src/imagecompare ' \
              '-t %s -i %s -w %d -h %d' % (template_img_path, match_img_path, cfg.DstImage_W, cfg.DstImage_H)
        self.loger.info("execute image match:%s" % cmd)
        with os.popen(cmd) as p:
            result_json_str = p.readlines()
            self.loger.info(result_json_str)
            result_json = json.loads(result_json_str[0])
            err_desc = rst_map[7]
            detail = []
            for img_result in result_json['result']:
                lubo_img_fullpath = img_result['lubo_image']
                img_file = os.path.basename(lubo_img_fullpath)
                oper_type = img_result['oper_type']
                if oper_type == 'match':
                    # 获取匹配点最大的模板项，返回结果已经是降序排序完成的
                    if img_result['match_result'] != None:
                        max_pro_match_image = img_result['match_result'][0]
                        match_t_image = max_pro_match_image['t_full_path']
                        match_image_dir = cfg.Image_Srv_Dir + "/" + match_id  # 图片服务器的路径
                        isexist = os.path.exists(match_image_dir)
                        if not isexist:
                            os.makedirs(match_image_dir)

                        # 转换图片格式并复制到图片服务器路径下
                        row_t_img = Image.open(match_t_image)
                        t_filename = os.path.basename(match_t_image)
                        basename = os.path.splitext(t_filename)[0]
                        jpg_name = basename + ".jpg"
                        dst_path = "%s/%s" % (match_image_dir, jpg_name)
                        self.loger.info("%s -> %s" % (match_t_image, dst_path))
                        row_t_img.save(dst_path)

                        # 生成结果消息
                        match_image_url = os.path.join(cfg.cfg.Match_Image_Base_URL, match_id + "/" + jpg_name)
                        item = {'image': img_file, 'status': 0 , 'desc': 'MatchSuccess',
                                'url': match_image_url}
                        detail.append(item)

                        # 插入匹配结果MatchResult表
                        lubo_f_num = max_pro_match_image['lubo_f_num']
                        match_cnt = max_pro_match_image['match_num']
                        template_f_num = max_pro_match_image['t_f_num']
                        template_fullpath = max_pro_match_image['t_full_path']
                        weigth = max_pro_match_image['weight']
                        sql = 'insert into MatchResult(MatchSessionID,ImageFileName,ImageFilePath,' \
                              'Status,ImageFeatureNum,MatchTemplateFeatureNum,MatchTemplateImagePath,' \
                              'MatchFeatureNum,Weight) values(\"%s\",\"%s\",\"%s\",%d,%d,%d,\"%s\",%d,%.3f)' %(
                              match_id, img_file, lubo_img_fullpath, 0, lubo_f_num, template_f_num,template_fullpath,
                              match_cnt, weigth)
                        row = []
                        DatabaseOpt.db.exesql(sql, row)
                    else:
                        item = {'image': img_file, 'status': 1, 'desc': 'MatchFailed', 'url': ""}
                        detail.append(item)
                elif oper_type == 'ocr':
                    rm_ocr_word_img_filename = img_file.replace("_ocr.", ".")
                    item = {'image': rm_ocr_word_img_filename, 'status': 0, 'desc': 'MatchSuccess', 'url': ""}
                    detail.append(item)
            result_json = {"Version": 1, "MsgID": id, "MsgType": "result",
                "DateTime": tm_str,    "TaskID": taskid,
                "MatchSessionID" : match_id, 'ResultName': 'MatchImage',
                "Result": {'Status': 7, 'Desc': err_desc, 'Detail': detail}}

            # 记录匹配任务的完成状态
            sql = "update MatchSession set MatchDoneTime=\"%s\" where MatchSessionID=\"%s\"" %(tm_str, match_id)
            row = []
            DatabaseOpt.db.exesql(sql, row)

        return result_json

    def gen_match_video_result_msg(self, id, result):
        match_video_path = self.request_head[id]['SavePath']
        if os.path.exists(match_video_path):
            FetchImage.fetch_image(match_video_path,1,cfg.DstImage_W,cfg.DstImage_H)
        rst_map = {6: "DownLoadImageFailed", 7: "MatchComplete", 8: "MatchFailed", 0: "Download Done"}
        tm_str = self.get_time_str()
        taskid = self.request_head[id]["TaskID"]
        match_id = self.request_head[id]["MatchSessionID"]
        err_desc = rst_map[result]
        result_json = {"Version": 1, "MsgID": id, "MsgType": "result",
            "DateTime": tm_str,    "TaskID": taskid,
            "MatchSessionID" : match_id, 'ResultName': 'MatchVideo',
            "Result": {'Status': result, 'Desc': err_desc}}
        return result_json

    def gen_match_video_test_result_msg(self, id, result, videofilename):
        rst_map = {6: "DownLoadImageFailed", 7: "MatchComplete", 8: "MatchFailed" }
        tm_str = self.get_time_str()
        request_head = self.request_head[id]
        match_id = self.request_head[id]["MatchSessionID"]
        err_desc = rst_map[result]
        detail = []
        for i in range(4):
            item = {'image': videofilename, 'status':0 , 'desc': 'MatchSuccess',
                    'url': 'http://www.test.com/test.jpg'}
            detail.append(item)
        result_json = {"Version": 1, "MsgID": id, "MsgType": "result",
            "DateTime": tm_str,    "TaskID": request_head["TaskID"],
            "MatchSessionID" : match_id, 'ResultName': 'MatchVideo',
            "Result": {'Status': result, 'Desc': err_desc, 'Detail': detail}}
        return result_json


    def get_time_str(self):
        tm = time.time()+28800
        tm_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(tm))
        return tm_str

    def load_uncomplate_match(self):
        '''检测未完成匹配任务并加入匹配对列'''
        rows = []
        sql = 'select MatchSessionID,TaskID,Type,ObjPath,ResultURL ' \
              'from MatchSession where MatchDoneTime is NULL ;'

        DatabaseOpt.db.exesql(sql, rows)
        if len(rows) == 0:
            return
        for row in rows[0]:
            self.loger.info('load uncomplate match task %s' % str(row))
            matchid = row[0]
            taskid = row[1]
            type = row[2]
            match_img_path = row[3]
            resultaddr = row[4]
            t_width = cfg.DstImage_W
            t_height = cfg.DstImage_H
            template_img_path = os.path.join(cfg.DownloadDir, taskid)
            if int(type) == 1:
                self.match_thread[self.match_thread_index].add_match_image_task(taskid, matchid, match_img_path,
                                                                                template_img_path, t_width,
                                                                                t_height, resultaddr)
                self.match_thread_index = (self.match_thread_index + 1) % len(self.match_thread)
            elif int(type) == 2:
                self.match_v_thread[self.match_v_thread_index].add_video_compare_task(taskid, matchid, match_img_path,
                                                                                      template_img_path, t_width,
                                                                                      t_height, resultaddr)
                self.match_v_thread_index = (self.match_v_thread_index + 1) % len(self.match_v_thread)



    def load_uncomplate_template_create(self):
        '''检测未完成模板创建任务'''
        rows =[]
        sql = 'select TaskID,TemplateID,TemplateURL,DownLoadFilePath,ResultURL,TemplateType from ' \
              'Template where DownloadDone is null or DownloadDone=0;'

        DatabaseOpt.db.exesql(sql, rows)
        if len(rows) == 0:
            return
        for row in rows[0]:
            self.loger.info('load uncomplate download task:%s'%(str(row)))
            task_id = row[0]
            template_id = row[1]
            dl_url = row[2]
            video_all_path = row[3]
            result_url = row[4]
            template_type = row[5]

            # 添加下载任务
            self.request_head[task_id] = {}
            self.request_head[task_id]['TaskID'] = task_id
            self.request_head[task_id]['TemplatePath'] = video_all_path
            self.request_head[task_id]['ResultURL'] = result_url
            self.request_head[task_id]['TemplateType'] = template_type
            self.dl_thread[self.dl_thread_index].add_download_task([dl_url], [video_all_path],
                                                                   task_id, "CreateTemplate")
            self.dl_thread_index = (self.dl_thread_index+1) % len(self.dl_thread)




if __name__ == '__main__':
    msg = Msg()
    msg.start()
    info = {"MsgHead":{"Version":1, "Invoker": "user1", "ResultURL": "http://10.7.75.78:8080/result.php",
            "MsgID": 12341, "MsgType": "request", "DateTime": "2018-02-26 12:00:00", "Cmd": "CreateTemplate",
            "Token": "da39a3ee5e6b4b0d3255bfef95601890afd80709"}, "TaskID": "DD18110001", "TemplateID": "15d8c0ab-caa9-11e8-9c79-0235d2b38928" ,
            "TemplateName": "可口可乐",
            "TemplateURL": "https://files.pythonhosted.org/package/78/d8/6e58a7130d457edadb753a0ea5708e411c100c7e94e72ad4802feeef735c/pip-1.5.4.tar.gz"
             }
    msg.add_task_queue(info)






