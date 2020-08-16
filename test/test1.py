import cv2
import imutils
import numpy as np
filename1 = "./image/IMG_1582.jpeg"
filename2 = "./image/test.jpg"
src = cv2.imread(filename2,1)
# gray scale 로 변환
gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
# canny edge detection
edges = imutils.auto_canny(src)
# 아래에서 위로 채우기
h, w = edges.shape[:2]
max_row_inds = h - np.argmax(edges[::-1], axis=0)
row_inds = np.indices((h, w))[0]
inds_after_edges = row_inds >= max_row_inds
filled_from_bottom = np.zeros((h, w),dtype=np.uint8)
filled_from_bottom[inds_after_edges] = 255
# 침식, 팽창 연산
vertical_size = int(w/30)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (vertical_size,vertical_size))
erosion = cv2.erode(filled_from_bottom,kernel,iterations = 1)
dilate = cv2.dilate(erosion, kernel, iterations=1)
dilate = cv2.GaussianBlur(dilate,(5,5),0)
# 비트연산
dst = cv2.bitwise_and(gray, gray, mask=dilate)
cv2.imshow("dst", dst)


cv2.waitKey(0)
cv2.destroyWindow()