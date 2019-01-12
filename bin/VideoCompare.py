# -*- coding:utf-8 -*-

import os
import sift
import time
import threading
import scheduler
import mylog
from queue import Queue
import FetchImage
import DatabaseOpt
from Resultpost import ResultSend
import numpy as np
from PIL import Image
import io
import traceback

class VideoCompare:
    def __init__(self, ImageSrvHomeDir, ImageSrvBaseUrl, name='matchvideo'):
        self.mt_queue = Queue()
        self.is_run = True
        self.logger = mylog.logger
        self.image_srv_home = ImageSrvHomeDir
        self.result_img_base_url = ImageSrvBaseUrl
        self.h_thread = threading.Thread(target=self.process)
        self.myname = name

    def process(self):
        try:
            self.video_compare_process()
        except Exception as e:
            fp = io.StringIO()
            traceback.print_exc(file=fp)
            message = fp.getvalue()
            self.logger.info("%s process except:%s" % (self.myname, message))

    def video_compare_process(self):
        while self.is_run:
            node = self.mt_queue.get()
            self.logger.info("%s process task:%s" % (self.myname, node))
            match_id = node["MatchSessionID"]
            match_video_path = node['MatchVideoPath']
            taskid = node['TaskID']
            template_img_path = node['TempatePath']
            template_w = node['Template_W']
            template_h = node['Template_H']
            Image_Srv_Dir = node['ImageSrvHome']
            Match_Image_Base_URL = node['ResultImageUrl']
            resultaddr = node['ResultCommitURL']
            match_image_dir = Image_Srv_Dir + "/" + match_id

            #  截取视频中的图片
            if os.path.exists(match_video_path):
                FetchImage.fetch_image(match_video_path, 1, template_w, template_h)
            else:
                self.logger.info("error:%s not exist!")
                continue

            #  获取截取的图片列表
            video_dir_name = os.path.dirname(match_video_path)
            lubo_img_ls = self.walk_dir(video_dir_name, ['.bmp'])

            #  通过特征文件文件名字的特征数量信息，找到特征点最多的那种图
            f_num_ls = []
            all_sift_file = self.walk_dir(template_img_path, ['.sift'])
            for sift_file in all_sift_file:
                filename = sift_file.split('/')[-1]
                start = filename.find('_')+1
                end = filename.find('.')
                f_num = filename[start:end]
                f_num_ls.append(int(f_num))
            arg_fnum = np.argsort(f_num_ls)
            target_f_file = all_sift_file[arg_fnum[-1]]
            target_file_f = target_f_file.split('/')[-1]
            target_file_index = target_file_f[:target_file_f.find('_')]
            template_file = os.path.join(template_img_path, "%s.bmp"%target_file_index)
            mylog.logger.info("%s start match:%s" % (self.myname, self.get_time_str()))
            mylog.logger.info("%s match info:lubo:%s(%d) template path:%s" % (self.myname, video_dir_name,
                                                                                len(lubo_img_ls), template_file))
            result = []
            num_ls = []
            for file in lubo_img_ls:
                cn1, cn2, cnt = sift.compare_sift(file, template_file)
                result.append([file, cn1, cn2, cnt])
                num_ls.append(cnt)
            maxmatch_cnt_index = np.argsort(num_ls)[-1]
            mylog.logger.info('%s(%s):%s match result:%s' % (self.myname, self.get_time_str(),
                                                             template_img_path, result[maxmatch_cnt_index]))

            match_lubo_image = result[maxmatch_cnt_index][0]
            l_f_num = result[maxmatch_cnt_index][1]
            t_f_num = result[maxmatch_cnt_index][2]
            m_f_num = result[maxmatch_cnt_index][3]
            detail = []
            weight = (2*m_f_num)/(l_f_num+t_f_num)
            if weight > 0.01:
                video_file = os.path.basename(video_dir_name)

                # 转换图片格式并复制到图片服务器路径下
                # 复制模板图
                row_t_img = Image.open(template_file)
                t_filename = os.path.basename(template_file)
                basename = os.path.splitext(t_filename)[0]
                jpg_name = basename + ".jpg"
                is_exist = os.path.exists(match_image_dir)
                if not is_exist:
                    os.makedirs(match_image_dir)
                dst_path = os.path.join(match_image_dir, jpg_name)
                self.logger.info("%s:%s -> %s" % (self.myname, template_file, dst_path))
                row_t_img.save(dst_path)
                match_image_url = os.path.join(Match_Image_Base_URL, match_id + "/" + jpg_name)
                item = {'image': video_file, 'status': 0 , 'desc': 'MatchSuccess',
                        'url': match_image_url}
                detail.append(item)

                # 复制录播图
                row_t_img = Image.open(match_lubo_image)
                l_filename = os.path.basename(match_lubo_image)
                basename = os.path.splitext(l_filename)[0]
                jpg_name = basename + ".jpg"
                dst_path = os.path.join(match_image_dir, jpg_name)
                self.logger.info("%s:%s -> %s" % (self.myname, match_lubo_image, dst_path))
                row_t_img.save(dst_path)
                match_image_url = os.path.join(Match_Image_Base_URL, match_id + "/" + jpg_name)
                item = {'image': video_file, 'status': 0 , 'desc': 'MatchSuccess',
                        'url': match_image_url}
                detail.append(item)
            else:
                item = {'image': video_file, 'status': 1 , 'desc': 'MatchFailed',
                        'url': ""}
                detail.append(item)

            # 发送结果消息
            rst_map = {6: "DownLoadImageFailed", 7: "MatchComplete", 8: "MatchFailed"}
            err_desc = rst_map[7]
            tm_str = self.get_time_str()
            MsgID = "RMI%d" % (int(time.time()))
            result_json = {"Version": 1, "MsgID": MsgID, "MsgType": "result",
                           "DateTime": tm_str,    "TaskID": taskid, "MatchSessionID" : match_id,
                           'ResultName': 'MatchVideo', "Result": {'Status': 7, 'Desc': err_desc,
                                                                  'Detail': detail}}

            # 插入匹配结果MatchResult表
            video_filename = os.path.basename(match_video_path)
            sql = 'insert into MatchResult(MatchSessionID,ImageFileName,ImageFilePath,' \
                  'Status,ImageFeatureNum,MatchTemplateFeatureNum,MatchTemplateImagePath,' \
                  'MatchFeatureNum,Weight) values(\"%s\",\"%s\",\"%s\",%d,%d,%d,\"%s\",%d,%.3f)' %(
                  match_id, video_filename, match_lubo_image, 0, l_f_num, t_f_num, template_file,
                  m_f_num, weight)
            row = []
            DatabaseOpt.db.exesql(sql, row)

            # 发现结果消息，并添加两个定时任务：在5分钟和30分钟后再次发送
            ResultSend.send_th(resultaddr, result_json)
            scheduler.timer_task.AddTimerTask(300, [resultaddr, result_json])
            scheduler.timer_task.AddTimerTask(1800, [resultaddr, result_json])

            # 记录匹配任务的完成状态
            sql = "update MatchSession set MatchDoneTime=\"%s\", MatchResultPath=\"%s\" " \
                  "where MatchSessionID=\"%s\"" % (tm_str, match_image_dir, match_id)
            row = []
            DatabaseOpt.db.exesql(sql, row)
            self.mt_queue.task_done()

    def add_video_compare_task(self, taskid, msi, match_video_path, template_path, t_width, t_height, result_commit_url):
        node = {}
        node["MatchSessionID"] = msi
        node['MatchVideoPath'] = match_video_path
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

    def walk_dir(self, train_path, filter):
        training_names = os.listdir(train_path)
        # Get all the path to the images and save them in a list
        # image_paths and the corresponding label in image_paths
        image_paths = []
        for training_name in training_names:
            ext_name = os.path.splitext(training_name)[1]
            if ext_name in filter:
                image_path = os.path.join(train_path, training_name)
                image_paths += [image_path]
        return image_paths
