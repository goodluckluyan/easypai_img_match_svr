# -*- coding:utf-8 -*-

import cv2
import numpy as np

img1 = cv2.imread('D:\\Project\easypai\\test_img\\bad_sample\\dd19010005\\6c2a9e5a1f80'
                  '\\be6b0bcb7ca8e1b666c5e79dfc3ec0eb.jpg', 0)
c_img2 = cv2.imread('D:\\Project\easypai\\test_img\\bad_sample\\dd19010005\\6c2a9e5a1f80'
                  '\\c96dbb94aed71ff6916de859800b015b.jpg')
img2 = cv2.cvtColor(c_img2,cv2.COLOR_RGB2GRAY)
img3 = cv2.imread('D:\\Project\easypai\\test_img\\bad_sample\\dd19010005\\6c2a9e5a1f80'
                  '\\d29364398160e9bc91a15aff956b5cb0.jpg', 0)
img4 = cv2.imread('D:\\Project\easypai\\test_img\\bad_sample\\dd19010005\\6c2a9e5a1f80'
                  '\\ed83e911906a7fcf846f212d2b5c945f.jpg', 0)



img1 = cv2.resize(img1,(704,576))
c_img2 = cv2.resize(c_img2,(704,575))
img2 = cv2.resize(img2,(704,576))
img3 = cv2.resize(img3,(704,576))
img4 = cv2.resize(img4,(704,576))
sum = np.zeros_like(img1, dtype=np.float)
print(img1.shape)
print(img2.shape)
print(img3.shape)
print(img4.shape)
print(sum.shape)
sum = sum + img1
sum = sum + img2
sum = sum + img3
sum = sum + img4

avg = sum/4
avg = avg.astype(np.uint8)

diff1 = img1-avg
diff2 = img2-avg
diff3 = img3-avg
diff4 = img4-avg
print(avg)
print(diff2)
ret , binary = cv2.threshold(diff2 ,90 ,255 ,cv2.THRESH_BINARY)

print(binary.dtype)
cv2.imshow('img1',binary)
cv2.waitKey(0)
cv2.destroyAllWindows()
_ ,contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cv2.drawContours(c_img2,contours,-1,(0,0,255))

cv2.imshow('img1',c_img2)
cv2.waitKey(0)
cv2.destroyAllWindows()


# cv2.imshow('img1',diff)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
