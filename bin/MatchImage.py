#!/usr/bin/python
#encoding:utf-8
from urllib import request
from urllib import error as urlerr
from queue import Queue
import threading
import os
from PIL import Image
import mylog
import json
import DatabaseOpt
from Resultpost import ResultSend
import time
import scheduler
from Config import cfg
import io
import traceback

class MatchImage:
    def __init__(self, ImageSrvHomeDir, ImageSrvBaseUrl, name='matchimage'):
        self.mt_queue = Queue()
        self.is_run = True
        self.logger = mylog.logger
        self.image_srv_home = ImageSrvHomeDir
        self.result_img_base_url = ImageSrvBaseUrl
        self.h_thread = threading.Thread(target=self.process)
        self.scheduler = scheduler.Scheduler()
        self.myname = name

    def process(self):
        try:
            self.match_process()
        except Exception as e:
            fp = io.StringIO()
            traceback.print_exc(file=fp)
            message = fp.getvalue()
            self.logger.info("%s process except:%s" % (self.myname, message))

    def match_process(self):
        while self.is_run:
            node = self.mt_queue.get()
            match_id = node["MatchSessionID"]
            match_img_path = node['MatchImagePath']
            taskid = node['TaskID']
            template_img_path = node['TempatePath']
            template_w = node['Template_W']
            template_h = node['Template_H']
            Image_Srv_Dir = node['ImageSrvHome']
            Match_Image_Base_URL = node['ResultImageUrl']
            resultaddr = node['ResultCommitURL']
            cmd = 'sudo %s -t %s -i %s -w %d -h %d' % (cfg.ImageCompareCmd,
                                                       template_img_path,
                                                       match_img_path,
                                                       template_w,
                                                       template_h)
            self.logger.info("%s execute image match:%s" % (self.myname, cmd))

            rst_map = {6: "DownLoadImageFailed", 7: "MatchComplete", 8: "MatchFailed"}
            tm_str = self.get_time_str()
            result_json_str = ''
            with os.popen(cmd) as p:
                result_json_str = p.readlines()
                self.logger.info("%s %s" % (self.myname, result_json_str))
            if len(result_json_str) > 0:
                result_json = json.loads(result_json_str[0])
                detail = []
                err_desc = rst_map[7]
                for img_result in result_json['result']:
                    lubo_img_fullpath = img_result['lubo_image']
                    img_file = os.path.basename(lubo_img_fullpath)
                    oper_type = img_result['oper_type']
                    if oper_type == 'match':
                        # 获取匹配点最大的模板项，返回结果已经是降序排序完成的
                        if img_result['match_result'] != None:
                            max_pro_match_image = img_result['match_result'][0]
                            match_t_image = max_pro_match_image['t_full_path']
                            match_image_dir = Image_Srv_Dir + "/" + match_id  # 图片服务器的路径
                            isexist = os.path.exists(match_image_dir)
                            if not isexist:
                                os.makedirs(match_image_dir)

                            # 转换图片格式并复制到图片服务器路径下
                            row_t_img = Image.open(match_t_image)
                            t_filename = os.path.basename(match_t_image)
                            basename = os.path.splitext(t_filename)[0]
                            jpg_name = basename + ".jpg"
                            dst_path = "%s/%s" % (match_image_dir, jpg_name)
                            self.logger.info("%s %s -> %s" % (self.myname, match_t_image, dst_path))
                            row_t_img.save(dst_path)

                            # 生成结果消息
                            match_image_url = os.path.join(Match_Image_Base_URL, match_id + "/" + jpg_name)
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
                                  'MatchFeatureNum,Weight,CreateTime) values(\"%s\",\"%s\",\"%s\",%d,%d,%d,\"%s\",%d,%.3f,' \
                                  '\"%s\")' %( match_id, img_file, lubo_img_fullpath, 0, lubo_f_num, template_f_num,template_fullpath,
                                  match_cnt, weigth, tm_str)
                            row = []
                            DatabaseOpt.db.exesql(sql, row)
                        else:
                            item = {'image': img_file, 'status': 1, 'desc': 'MatchFailed', 'url': ""}
                            detail.append(item)
                    elif oper_type == 'ocr':
                        rm_ocr_word_img_filename = img_file.replace("_ocr.", ".")
                        item = {'image': rm_ocr_word_img_filename, 'status': 0, 'desc': 'MatchSuccess', 'url': ""}
                        detail.append(item)

                # 发送结果消息
                if len(detail) > 0:
                    MsgID = "RMI%d" % (int(time.time()))
                    result_json = {"Version": 1, "MsgID": MsgID, "MsgType": "result",
                                   "DateTime": tm_str,    "TaskID": taskid, "MatchSessionID" : match_id,
                                   'ResultName': 'MatchImage', "Result": {'Status': 7, 'Desc': err_desc,
                                                                          'Detail': detail}}
                else:
                    err_desc = rst_map[8]
                    MsgID = "RMI%d" % (int(time.time()))
                    result_json = {"Version": 1, "MsgID": MsgID, "MsgType": "result",
                                   "DateTime": tm_str, "TaskID": taskid, "MatchSessionID" : match_id,
                                   'ResultName': 'MatchImage', "Result": {'Status': 8, 'Desc': err_desc}
                                   }

                # 发现结果消息，并添加两个定时任务：在5分钟和30分钟后再次发送
                ResultSend.send(resultaddr, result_json)
                scheduler.timer_task.AddTimerTask(300, [resultaddr, result_json])
                scheduler.timer_task.AddTimerTask(1800, [resultaddr, result_json])

                # 记录匹配任务的完成状态
                sql = "update MatchSession set MatchDoneTime=\"%s\" where MatchSessionID=\"%s\"" %(tm_str, match_id)
                row = []
                DatabaseOpt.db.exesql(sql, row)
            self.mt_queue.task_done()

    def add_match_image_task(self, taskid, msi, match_img_path, template_path, t_width, t_height, result_commit_url):
        node = {}
        node["MatchSessionID"] = msi
        node['MatchImagePath'] = match_img_path
        node['TaskID'] = taskid
        node['TempatePath'] = template_path
        node['Template_W'] = t_width
        node['Template_H'] = t_height
        node['ImageSrvHome'] = self.image_srv_home
        node['ResultImageUrl'] = self.result_img_base_url
        node['ResultCommitURL'] = result_commit_url
        self.mt_queue.put(node)

    def start(self):
        self.h_thread.start()
        scheduler.timer_task.start()

    def end(self):
        self.is_run = False

    def get_time_str(self):
        tm = time.time()+28800
        tm_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(tm))
        return tm_str

