#-*- coding:utf-8 -*-
import cv2
import numpy as np
import os
import sys
import mylog
import copy


def sift_kp(image):
    gray_image = image #cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sift=cv2.xfeatures2d.SIFT_create()
    kp, des = sift.detectAndCompute(image,None)
    kp_image = cv2.drawKeypoints(gray_image, kp, None)
    return kp_image, kp, des


def get_good_match(des1, des2):
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2) # des1为模板图，des2为匹配图
    matches = sorted(matches,key=lambda x:x[0].distance/x[1].distance)
    good = []
    for m, n in matches:
        if m.distance < 0.8 * n.distance:
            good.append(m)

    return good

# 单项匹配
def compare_sift(im1, im2):
    img1 = cv2.imread(im1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(im2, cv2.IMREAD_GRAYSCALE)

    _, kp1, des1 = sift_kp(img1)
    _, kp2, des2 = sift_kp(img2)
    #if len(des1) > 0 and len(des2) > 0: # des1/2 有可能是None 也有可能是np.array
    if np.array(des1 == None).any() or np.array(des2 == None).any():
           return 0, 0, 0

    goodMatch = get_good_match( des1, des2)
    exact_match = 0
    if len(goodMatch) > 10:
        ptsA = np.float32([kp1[m.queryIdx].pt for m in goodMatch]).reshape(-1, 1, 2)
        ptsB = np.float32([kp2[m.trainIdx].pt for m in goodMatch]).reshape(-1, 1, 2)
        ransacReprojThreshold = 10
        H, status = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, ransacReprojThreshold)
        exact_match = np.sum(np.array(status[:, 0] == 1, dtype=np.int))

    return len(des1), len(des2), exact_match

# 双向匹配
def compare_sift_bi(im1 , im2 ,display = False):
    img1 = cv2.imread(im1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(im2, cv2.IMREAD_GRAYSCALE)

    _, kp1, des1 = sift_kp(img1)
    _, kp2, des2 = sift_kp(img2)
    if np.array(des1 == None).any() or np.array(des2 == None).any():
           return 0, 0, 0, 0 ,0

    goodMatch = get_good_match(des1, des2)
    match_tuple_set = set()
    if len(goodMatch) > 10:
        # 找到单应矩阵使用ranscac进行筛选
        ptsA = np.float32([kp1[m.queryIdx].pt for m in goodMatch]).reshape(-1, 1, 2)
        ptsB = np.float32([kp2[m.trainIdx].pt for m in goodMatch]).reshape(-1, 1, 2)
        ransacReprojThreshold = 10
        H, status = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, ransacReprojThreshold)

        # 找到精确匹配项
        match_exact = status[:, 0] == 1
        goodMatch = [goodMatch[i] for i in range(len(match_exact)) if match_exact[i]]

        for m in goodMatch :
            kp1_tuple = (int(kp1[m.queryIdx].pt[0]), int(kp1[m.queryIdx].pt[1]))
            kp2_tuple = (int(kp2[m.trainIdx].pt[0]), int(kp2[m.trainIdx].pt[1]))
            match_tuple_set.add((kp1_tuple, kp2_tuple))

        #计算质心并计算和质心的距离，再计算距离的均值，从而描述两边匹配点的离散程度
        #ptsA = np.float32([kp1[m.queryIdx].pt for m in goodMatch]).reshape(-1, 1, 2)
        #ptsB = np.float32([kp2[m.trainIdx].pt for m in goodMatch]).reshape(-1, 1, 2)
        # ptsA = ptsA.reshape((-1, 2))
        # ptsB = ptsB.reshape((-1, 2))
        # avg_ptsA = sum(ptsA)/len(ptsA)
        # avg_ptsB = sum(ptsB)/len(ptsB)
        # square_a = (ptsA - avg_ptsA)**2
        # square_b = (ptsB - avg_ptsB)**2
        # sum_a = np.sum(square_a, axis=1)
        # sum_b = np.sum(square_b, axis=1)
        # dis_a = np.sqrt(sum_a)
        # dis_b = np.sqrt(sum_b)

        # 显示匹配点
        if display:
            goodMatch = np.expand_dims(goodMatch, 1)
            img3 = cv2.drawMatchesKnn(img1, kp1, img2, kp2, goodMatch, None, flags=2)
            cv2.imshow('img', img3)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    goodMatch_bi = get_good_match(des2, des1)
    match_tuple_bi_set = set()
    if len(goodMatch_bi) > 10:
        # 找到单应矩阵使用ranscac进行筛选
        ptsA = np.float32([kp2[m.queryIdx].pt for m in goodMatch_bi]).reshape(-1, 1, 2)
        ptsB = np.float32([kp1[m.trainIdx].pt for m in goodMatch_bi]).reshape(-1, 1, 2)
        ransacReprojThreshold = 10
        H, status = cv2.findHomography(ptsA, ptsB, cv2.RANSAC, ransacReprojThreshold)

        # 找到精确匹配项
        match_exact = status[:, 0] == 1
        goodMatch_bi = [goodMatch_bi[i] for i in range(len(match_exact)) if match_exact[i]]

        for m in goodMatch_bi :
            kp2_tuple = (int(kp2[m.queryIdx].pt[0]), int(kp2[m.queryIdx].pt[1]))
            kp1_tuple = (int(kp1[m.trainIdx].pt[0]), int(kp1[m.trainIdx].pt[1]))
            match_tuple_bi_set.add((kp1_tuple, kp2_tuple))

        if display:
            goodMatch_bi = np.expand_dims(goodMatch_bi, 1)
            img3 = cv2.drawMatchesKnn(img2, kp2, img1, kp1, goodMatch_bi, None, flags=2)
            cv2.imshow('img', img3)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    # print('a->b:%d'%(len(match_tuple_set)), match_tuple_set)
    # print('b->a:%d'%(len(match_tuple_bi_set)), match_tuple_bi_set)
    bi_match_pt = match_tuple_bi_set & match_tuple_set

    return len(des1), len(des2), len(goodMatch),len(goodMatch_bi), len(bi_match_pt)


def walk_dir(train_path, filter):

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
    num_ls = []
    for file in all_file:
        cn1, cn2, cnt=compare_sift(file,target_file)
        mylog.logger.info("%s %s %d %d %d"%(file, target_file, cn1,cn2,cnt))
        result.append([file, cn1, cn2, cnt])
        num_ls.append(cnt)
    mylog.logger.info('result:%s' % result[np.argsort(num_ls)[-1]])



if __name__ == '__main__':

    check_file = walk_dir('D:\\Project\\easypai\\test_img\\bad_sample\\dd19010005\\b370582f0b4a', ['.jpg'])
    t_img = 'D:\\Project\\easypai\\test_img\\dd19010005\\11.bmp'
    for l_img in check_file:
        print(t_img)
        print(l_img)
        cn1, cn2, ab_m,ba_m,match=compare_sift_bi(t_img, l_img,True)
        print(cn1, cn2, ab_m,ba_m, match)
        # cn1, cn2, match = compare_sift(t_img,l_img)
        # print('a->b',cn1, cn2,  match)
        # cn1, cn2, match = compare_sift(l_img,t_img)
        # print('b->a', cn1, cn2,  match)



    # dir_ls = ['/home/ubuntu/bow_test/binjiang',
    #           '/home/ubuntu/bow_test/bolong', '/home/ubuntu/bow_test/feiyada',
    #           '/home/ubuntu/bow_test/fute', '/home/ubuntu/bow_test/jiedei',
    #           '/home/ubuntu/bow_test/note', '/home/ubuntu/bow_test/oppo',
    #           '/home/ubuntu/bow_test/richan', '/home/ubuntu/bow_test/ruijie']
    # for d in dir_ls:
    #     if os.path.isdir(d):
    #         mylog.logger.info("==========compare: %s=========="%d)
    #         test(d)
    #         mylog.logger.info('========================================================')
    # check_file = walk_dir('D:\\Project\\easypai\\test_img\\920b4e543b76', ['.jpg'])
    # for file in check_file:
    #     ret = compare_sift(file, 'D:\\Project\\easypai\\test_img\\dd19010005\\4.bmp')
    #     print(file,ret)


    # cn1,cn2,match,dis1,dis2=compare_sift_d(l_img, t_img)
    # print(cn1, cn2, match ,dis1, dis2)
    # img = cv2.imread('D:\\Project\\easypai\\14.bmp',cv2.IMREAD_GRAYSCALE)
    # print(img.shape)
    # img_t = img.T
    # cv2.imshow('tranpose', img_t)
    # cv2.waitKey()
    #
    #
    # cv2.imshow('flip', cv2.flip(img_t,1,dst=None))
    # cv2.waitKey()
