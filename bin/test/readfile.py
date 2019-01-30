# -*- coding:utf-8 -*-
import os
import json
import mylog
from PIL import Image, ExifTags

p = open('.\\format.log','r')
# print(p.read())
j = json.loads(p.read())
# for l in p.readlines():
#     print(l)
mylog.logger.info(j)


img = Image.open('D:\\Project\\easypai\\IMG_20181226_065109.jpg')


for orientation in ExifTags.TAGS.keys() :
    if ExifTags.TAGS[orientation] == 'Orientation' : break

exif=dict(img._getexif())
print(orientation)
print(exif[orientation])
for i in exif.keys():
     print(i,exif[i])


