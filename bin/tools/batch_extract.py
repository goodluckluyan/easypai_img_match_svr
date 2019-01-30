#-*- coding:utf-8 -*-
import os
import time
import sys

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

if __name__=='__main__':
    img_ls = walk_dir(sys.argv[1],['.bmp'])
    for img_name in img_ls:
        cmd = '/root/easypai/extrace/extrace -t sift -i %s'%(img_name)
        print(cmd)
        os.system(cmd)