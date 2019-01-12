#-*- coding:utf-8 -*-
import cv2
import numpy as np
import os
import sys
import mylog

def sift_kp(image):
    gray_image = image #cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sift=cv2.xfeatures2d.SIFT_create()
    kp,des = sift.detectAndCompute(image,None)
    kp_image = cv2.drawKeypoints(gray_image, kp, None)
    return kp_image,kp,des


def get_good_match(des1, des2):
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2) # des1为模板图，des2为匹配图
    matches = sorted(matches,key=lambda x:x[0].distance/x[1].distance)
    good = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)
    return good


def siftImageAlignment(img1,img2):
   _,kp1,des1 = sift_kp(img1)
   _,kp2,des2 = sift_kp(img2)
   goodMatch = get_good_match(des1,des2)
   if len(goodMatch) > 4:
       ptsA= np.float32([kp1[m.queryIdx].pt for m in goodMatch]).reshape(-1, 1, 2)
       ptsB = np.float32([kp2[m.trainIdx].pt for m in goodMatch]).reshape(-1, 1, 2)
       ransacReprojThreshold = 4
       H, status =cv2.findHomography(ptsA,ptsB,cv2.RANSAC,ransacReprojThreshold);
       imgOut = cv2.warpPerspective(img2, H, (img1.shape[1],img1.shape[0]),flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
   return imgOut,H,status

def compare_sift(im1,im2):
    img1 = cv2.imread(im1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(im2, cv2.IMREAD_GRAYSCALE)

    _, kp1, des1 = sift_kp(img1)
    _, kp2, des2 = sift_kp(img2)
    #if len(des1) > 0 and len(des2) > 0:
    if np.array(des1 == None).any() or np.array(des2 == None).any():
           return 0
    goodMatch = get_good_match(des1, des2)
    return len(des1),len(des2),len(goodMatch)

    #img3 = cv2.drawMatches(img1, kp1, img2, kp2, goodMatch[:5], None, flags=2)
    #----or----
    #goodMatch = np.expand_dims(goodMatch,1)
    #img3 = cv2.drawMatchesKnn(img1, kp1, img2, kp2, goodMatch[:5], None, flags=2)

    # cv2.imshow('img',img3)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

def walk_dir(train_path,filter):

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

def test(t_path):
    compare_dir = '/home/ubuntu/bow_test/lubo'
    all_file = walk_dir(compare_dir, ['.png'])
    all_sift_file = walk_dir(t_path, ['.sift'])
    f_num_ls = []
    if len(all_sift_file) == 0:
        raw_img_path = walk_dir(t_path, ['.bmp'])
        for raw in raw_img_path:
            cmd = '/home/ubuntu/easypai/extrace/extrace -t sift -i %s'%raw
            mylog.logger.info(cmd)
            os.system(cmd)
        all_sift_file = walk_dir(t_path, ['.sift'])
    mylog.logger.info(all_sift_file)
    for sift_file in all_sift_file:
        filename = sift_file.split('/')[-1]
        start = filename.find('_')+1
        end = filename.find('.')
        f_num = filename[start:end]
        f_num_ls.append(int(f_num))
    arg_fnum = np.argsort(f_num_ls)
    print(arg_fnum)
    print(f_num_ls)
    target_f_file = all_sift_file[arg_fnum[-1]]
    target_file_f = target_f_file.split('/')[-1]
    target_file_index = target_file_f[:target_file_f.find('_')]
    target_file = os.path.join(t_path, "%s.bmp"%target_file_index)

    mylog.logger.info("template path:%s"%target_file)
    result = []
    num_ls  = []
    for file in all_file:
        cn1,cn2,cnt=compare_sift(file,target_file)
        mylog.logger.info("%s %s %d %d %d"%(file, target_file, cn1,cn2,cnt))
        result.append([file, cn1, cn2, cnt])
        num_ls.append(cnt)
    mylog.logger.info('result:%s'%result[np.argsort(num_ls)[-1]])


if __name__ == '__main__':

    dir_ls = ['/home/ubuntu/bow_test/binjiang',
              '/home/ubuntu/bow_test/bolong','/home/ubuntu/bow_test/feiyada',
              '/home/ubuntu/bow_test/fute','/home/ubuntu/bow_test/jiedei',
              '/home/ubuntu/bow_test/note','/home/ubuntu/bow_test/oppo',
              '/home/ubuntu/bow_test/richan','/home/ubuntu/bow_test/ruijie']
    for d in dir_ls:
        if os.path.isdir(d):
            mylog.logger.info("==========compare: %s=========="%d)
            test(d)
            mylog.logger.info('========================================================')
