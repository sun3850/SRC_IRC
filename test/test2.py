import cv2
import imutils
import numpy as np
cap = cv2.VideoCapture(0)
while(cap.isOpened()):
    ret, src = cap.read()
    if not (ret): continue
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    # canny edge detection
    edges = imutils.auto_canny(gray)
    cv2.imshow("canny", edges)
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
    erosion = cv2.erode(filled_from_bottom,kernel, iterations=1)
    dilate = cv2.dilate(erosion, kernel, iterations=1)
    mask = cv2.GaussianBlur(dilate,(5,5),0)
    # 비트연산
    dst = cv2.bitwise_and(gray, gray, mask=mask)
    cv2.imshow("dst", dst)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()
