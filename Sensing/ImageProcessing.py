import cv2
import numpy as np
from threading import Thread

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

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
        self.src = np.zeros((height, width, 3), np.uint8)

    def getBinImage(self, color="RED"):
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
        img_result = cv2.bitwise_and(img, img, mask=img_mask)
        cv2.imshow("result", img_result)
        # cv2.imshow("mask", img_mask)
        cv2.waitKey(1)

    def updateImage(self, src):
        self.src = src

    def getImage(self):
        return self.src.copy()

    def isObstacle(self, obstacle):
        return True

    def traceObstacle(self, obstacle): pass

    def isYellowLine(self): return False

    def detectYellowLine(self):
        self.src = self.updateImage()

    def imshow(self):
        while(True):
            cv2.imshow("debug", self.getImage())
            cv2.waitKey(1)

    def countObstacle(self, obstacle):
        pass

    def positionOfObstacle(self): pass


if __name__ == "__main__":
    from Sensing.CameraSensor import Camera
    cam = Camera(1)
    imageProcessor = ImageProcessor(cam.width, cam.height)
    cam_t = Thread(target=cam.produce, args=(imageProcessor,))  # 카메라 센싱 쓰레드
    cam_t.start()  # 카메라 프레임 공급 쓰레드 동작
    show_t = Thread(target=imageProcessor.imshow)
    show_t.start()

    while(True):
        imageProcessor.getBinImage(color="RED1")
    pass