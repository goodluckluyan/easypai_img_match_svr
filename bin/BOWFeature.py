#!/usr/local/bin/python2.7
# -*- coding:utf-8 -*-
#python findFeatures.py -t dataset/train/

import argparse as ap
import cv2
import numpy as np
import os
from sklearn.externals import joblib
from scipy.cluster.vq import *
from sklearn import preprocessing
import sift
import time
def gen_bow_feature_and_save(image_paths, save_path,numWords=100):
    '''
    此函数对指定目录中的图像进行bow操作，并保存聚类结果即：
    图像bow向量、图像路径、特征中心数量、中心视觉词
    '''

    #training_names = os.listdir(train_path)

    # Get all the path to the images and save them in a list
    # image_paths and the corresponding label in image_paths
    # image_paths = []
    # for training_name in training_names:
    #     ext_name = os.path.splitext(training_name)[1]
    #     if ext_name in [".bmp"]:
    #         image_path = os.path.join(train_path, training_name)
    #         image_paths += [image_path]

    # Create feature extraction and keypoint detector objects
    fea_det = cv2.xfeatures2d.SIFT_create()

    # List where all the descriptors are stored
    des_list = []
    for image_path in image_paths:
        im = cv2.imread(image_path)
        print( "Extract SIFT of %s image" %(image_path))
        kpts, des = fea_det.detectAndCompute(im,None)
        if np.array(des == None).any():
           continue
        if des.shape[0] > 0:
            des_list.append((image_path, des))

    # Stack all the descriptors vertically in a numpy array
    descriptors = des_list[0][1]
    for image_path, descriptor in des_list[1:]:
        descriptors = np.vstack((descriptors, descriptor))

    # Perform k-means clustering
    #print "Start k-means: %d words, %d key points" %(numWords, descriptors.shape[0])
    voc, variance = kmeans(descriptors, numWords, 1)

    # Calculate the histogram of features
    im_features = np.zeros((len(image_paths), numWords), "float32")
    for i in range(len(des_list)):
        words, distance = vq(des_list[i][1], voc)
        for w in words:
            im_features[i][w] += 1

    # Perform Tf-Idf vectorization
    nbr_occurences = np.sum( (im_features > 0) * 1, axis = 0)
    idf = np.array(np.log((1.0*len(image_paths)+1) / (1.0*nbr_occurences + 1)), 'float32')

    # Perform L2 normalization
    # im_features = im_features*idf
    im_features = preprocessing.normalize(im_features, norm='l2')

    # save to file
    bowf_save_path = os.path.join(save_path, 'bowf.pkl')
    joblib.dump((im_features, image_paths, idf, numWords, voc), bowf_save_path, compress=3)
    return bowf_save_path


def search_from_bow_feature_set(bow_feature_set_path,image_path):

    # Load the classifier, class names, scaler, number of clusters and vocabulary
    im_features, image_paths, idf, numWords, voc = joblib.load(bow_feature_set_path)

    # Create feature extraction and keypoint detector objects
    fea_det = cv2.xfeatures2d.SIFT_create()

    # List where all the descriptors are stored
    im = cv2.imread(image_path,0)
    # height = im.shape[0]
    # width = im.shape[1]
    # kuadu_w = width//3
    # start_w = width//2-kuadu_w
    # end_w = width//2+kuadu_w
    # kuadu_h = height//3
    # start_h = height//2 - kuadu_h
    # end_h = height//2 + kuadu_h
    # #print(start_h,end_h,start_w,end_w)
    # block_img = im[start_h:end_h, start_w:end_w]
    kpts, des = fea_det.detectAndCompute(im, None)

    # 生成bow特征
    test_features = np.zeros((1, numWords), "float32")
    words, distance = vq(des, voc)
    for w in words:
        test_features[0][w] += 1

    # Perform Tf-Idf vectorization and L2 normalization
    #test_features = test_features*idf
    test_features = preprocessing.normalize(test_features, norm='l2')

    # 计算余弦距离
    score = np.dot(test_features, im_features.T)
    rank_ID = np.argsort(-score)
    target_index = rank_ID[0][0]
    #print(score[0][target_index])

    if score[0][target_index] > 0.8:
        match_cnt = sift.compare_sift(image_path,image_paths[target_index])
        print(image_path, image_paths[target_index], score[0][target_index],match_cnt)
        return [image_path, image_paths[target_index], score[0][target_index], match_cnt]
    else:
        return []


def walk_dir(train_path):

    training_names = os.listdir(train_path)
    # Get all the path to the images and save them in a list
    # image_paths and the corresponding label in image_paths
    image_paths = []
    for training_name in training_names:
        ext_name = os.path.splitext(training_name)[1]
        if ext_name in [".png"]:
            image_path = os.path.join(train_path, training_name)
            image_paths += [image_path]
    return image_paths

if __name__ == '__main__':
    start = time.time()
    train_path = 'D:\\bow_test\\bolong'
    train_path_ls = walk_dir(train_path)
    save_path = gen_bow_feature_and_save(train_path_ls, train_path, 100)
    #save_path = os.path.join(train_path, 'bowf.pkl')

    lubo_path = 'D:\\bow_test\\lubo'
    lubo_path_ls = walk_dir(lubo_path)
    match_result_ls = []
    for file_path in lubo_path_ls:
        node = search_from_bow_feature_set(save_path, file_path)
        if len(node)>0:
            match_result_ls.append(node)
    match_result_ls = sorted(match_result_ls, key=lambda x:x[3])
    print(match_result_ls[-5:])
    print(time.time()-start)
