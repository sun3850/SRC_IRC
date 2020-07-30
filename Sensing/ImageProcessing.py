import cv2
import numpy as np
from threading import Thread

DONT_DEBUG = False
DEBUG = True
#COLORS HSV THRESHOLD RANGE
COLORS = dict()
COLORS["YELLOW"] = {
    "lower" : [[],[],[]],
    "upper" : [[],[],[]]
}
COLORS["GREEN"] = {
    "lower" : [[],[],[]],
    "upper" : [[],[],[]]
}
COLORS["BLUE"] = {
    "lower" : [[],[],[]],
    "upper" : [[],[],[]]
}
COLORS["RED1"] = {
    "upper" : [[181,163,200],[181,163,200],[181,163,200]],
    "lower" : [[56,75,164],[56,75,164],[56,75,164]]
}
COLORS["RED2"] = {
    "lower" : [[139,145,186],[139,145,186],[139,145,186]],
    "upper" : [[55,94,149],[55,94,149],[55,94,149]]
}
COLORS[""] = {
    "lower" : [[],[],[]],
    "upper" : [[],[],[]]
}
COLORS[""] = {
    "lower" : [[],[],[]],
    "upper" : [[],[],[]]
}
COLORS[""] = {
    "lower" : [[],[],[]],
    "upper" : [[],[],[]]
}



class ImageProcessor:
    def __init__(self, height, width):
        self.__src = np.zeros((height, width, 3), np.uint8)

    def getBinImage(self, color="RED", debug=False): # 인자로 넘겨 받은 색상만 남기고 리턴
        img = self.getImage()
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
        lower1, lower2, lower3  = COLORS[color]["lower"]
        upper1, upper2, upper3 = COLORS[color]["upper"]
        img_mask1 = cv2.inRange(img_hsv, np.array(lower1), np.array(upper1))
        img_mask2 = cv2.inRange(img_hsv, np.array(lower2), np.array(upper2))
        img_mask3 = cv2.inRange(img_hsv, np.array(lower3), np.array(upper3))
        temp = cv2.bitwise_or(img_mask1, img_mask2)
        img_mask = cv2.bitwise_or(img_mask3, temp)
        k = (11, 11)
        kernel = np.ones(k, np.uint8)
        img_mask = cv2.morphologyEx(img_mask, cv2.MORPH_OPEN, kernel)
        img_mask = cv2.morphologyEx(img_mask, cv2.MORPH_CLOSE, kernel)
        img_result = cv2.bitwise_and(img, img, mask=img_mask) # 해당 색상값만 남기기

        if(debug):
            self.debug(img_result)

        return img_result

    def updateImage(self, src): # 카메라 쓰레드가 fresh 이미지를 계속해서 갱신해줌
        self.__src = src

    def debug(self, result): # 디버그용 (영상을 출력해서 봐야할때)
        cv2.imshow("debug", result)
        cv2.waitKey(1)

    def getImage(self): # 이미지를 필요로 할때
        return self.__src.copy()



if __name__ == "__main__":
    from Sensing.CameraSensor import Camera
    cam = Camera(1)
    imageProcessor = ImageProcessor(cam.width, cam.height)
    cam_t = Thread(target=cam.produce, args=(imageProcessor,))  # 카메라 센싱 쓰레드
    cam_t.start()  # 카메라 프레임 공급 쓰레드 동작

    while(True):
        i = imageProcessor.getBinImage(color="RED1", debug=DEBUG)
    pass