# -*- coding:utf-8 -*-

import configparser

class config:
    def __init__(self):
        self.DB_Host = '127.0.0.1'
        self.DB_Port = 3306
        self.DB_User = 'root'
        self.DB_Password = 'easypai123'
        self.DB_Name = 'easypai'
        self.DownloadDir = "/root/easypai/bin/template/"
        self.Image_Srv_Dir = '/usr/share/nginx/html'
        self.DownloadMatchSessionDir = "/root/easypai/bin/matchsession/"
        self.Match_Image_Base_URL = 'http://39.98.190.155:8088/'
        self.Feature_type = 'sift'
        self.DstImage_W = 704
        self.DstImage_H = 576
        self.MatchImageSynProcess = 0
        self.GET_IMAGE_FREQUECE_FROM_VIDEO = 1.0  # 从视频中提取图像的频率 n:表示每秒n帧图像
        self.ImageCompareCmd = './ImageCompare'
        self.FeatureExtractCmd = './extrace'
        self.ffmpeg_Path = '/usr/bin/ffmpeg'
        self.ffprob_Path = '/usr/bin/ffprobe'
        self.cf = configparser.ConfigParser()

    def readcfg(self, cfg_path):
        self.cf.read(cfg_path)
        self.DB_Host = self.cf.get('db', 'db_host')
        self.DB_Port = self.cf.get('db', 'db_port')
        self.DB_User = self.cf.get('db', 'db_user')
        self.DB_Password = self.cf.get('db', 'db_password')
        self.DB_Name = self.cf.get('db', 'db_name')

        self.DownloadDir = self.cf.get('path', 'dir_template_download')
        self.Image_Srv_Dir = self.cf.get('path', 'dir_image_srv')
        self.DownloadMatchSessionDir = self.cf.get('path', 'dir_match_session')
        self.Match_Image_Base_URL = self.cf.get('path', 'url_base_image_srv')
        self.ImageCompareCmd = self.cf.get('path', 'image_compare_cmd_path')
        self.FeatureExtractCmd = self.cf.get('path', 'extract_feature_cmd_path')

        self.Feature_type = self.cf.get('process', 'feature_type')
        self.DstImage_W = self.cf.getint('process', 'dst_image_width')
        self.DstImage_H = self.cf.getint('process', 'dst_image_height')
        self.MatchImageSynProcess = self.cf.getint('process', 'synprocess_process')
        self.GET_IMAGE_FREQUECE_FROM_VIDEO = self.cf.get('process', 'get_image_frequece')


cfg=config()

if __name__ == '__main__':
    cfg.readcfg('./easypai.cfg')
    print(cfg.DB_Name, cfg.DB_Host)