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
COLORS["RED"] = {
    "upper" : [[181,255,107],[181,255,107],[181,255,107]],
    "lower" : [[125,163,32],[125,163,32],[125,163,32]]
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

class Target():
    def __init__(self, stats=None, centroid=None):
        self.x,self.y,self.width,self.height,self.area = stats
        self.centerX, self.centerY = int(centroid[0]), int(centroid[1])

    def getDistance(self, baseline):
        (bx, by) = baseline
        return (bx - self.centerX, by - self.centerY)



class ImageProcessor:
    def __init__(self, height, width):
        self.__src = np.zeros((height, width, 3), np.uint8)
        self.targets = []

    def getBinImage(self, color="RED", debug=False): # 인자로 넘겨 받은 색상만 남기고 리턴
        img = self.getImage()
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
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

    def findTarget(self, color="RED", debug = False):
        # 범위 값으로 HSV 이미지에서 마스크를 생성합니다.
        img = self.getImage()
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower1, lower2, lower3 = COLORS[color]["lower"]
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
        img_result = cv2.bitwise_and(img, img, mask=img_mask)  # 해당 색상값만 남기기
        if(debug):
            self.debug(img_result)
        # 라벨링
        _, _, stats, centroids = cv2.connectedComponentsWithStats(img_mask, connectivity=8)
        for idx, centroid in enumerate(centroids):  # enumerate 함수는 순서가 있는 자료형을 받아 인덱스와 데이터를 반환한다.
            if stats[idx][0] == 0 and stats[idx][1] == 0:
                continue

            if np.any(np.isnan(centroid)):  # 배열에 하나이상의 원소라도 참이라면 true (즉, 하나이상의 중심점이 숫자가 아니면)
                continue
            _, _, _, _, area = stats[idx]
            if area > 100:
                self.targets.append(Target(stats[idx], centroid))  #
        if self.targets:
            self.targets.sort(key=lambda x: x.y)
            target = self.targets[0]
            return target
        else:
            return None



if __name__ == "__main__":
    from Sensing.CameraSensor import Camera
    cam = Camera(1)
    imageProcessor = ImageProcessor(cam.width, cam.height)
    cam_t = Thread(target=cam.produce, args=(imageProcessor,))  # 카메라 센싱 쓰레드
    cam_t.start()  # 카메라 프레임 공급 쓰레드 동작

    while(True):
        i = imageProcessor.getBinImage(color="RED1", debug=DEBUG)
    pass
