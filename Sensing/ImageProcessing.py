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
    "upper" : [[182,255,190],[182,255,190],[182,255,190]],
    "lower" : [[102,163,68],[102,163,68],[102,163,68]]
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
        # img_result = cv2.bitwise_and(img, img, mask=img_mask) # 해당 색상값만 남기기

        if(debug):
            self.debug(img_mask)

        return img, img_mask
    def updateImage(self, src): # 카메라 쓰레드가 fresh 이미지를 계속해서 갱신해줌
        self.__src = src

    def debug(self, result): # 디버그용 (영상을 출력해서 봐야할때)
        cv2.imshow("debug", result)
        cv2.waitKey(1)

    def getImage(self): # 이미지를 필요로 할때
        return self.__src.copy()

    def detectTarget(self, color="RED", debug = False):
        targets = [] # 인식한 타깃들을 감지
        img, img_mask = self.getBinImage(color=color)
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
                targets.append(Target(stats[idx], centroid))  #
        if targets: # 타깃이 인식 됐다면 제일 가까운놈 리턴
            targets.sort(key=lambda x: x.y+x.height, reverse=True) # 인식된 애들중 가까운 놈 기준으로 정렬
            target = targets[0] # 제일 가까운 놈만 남김
            if(debug):
                cv2.circle(img, (target.centerX, target.centerY), 10, (0, 255, 0), 10)
                cv2.rectangle(img, (target.x, target.y), (target.x + target.width, target.y + target.height), (0, 255, 0))
                self.debug(img)
            return target
        else:# 인식된 놈이 없다면 None 리턴
            if(debug):
                cv2.putText(img, "** NO TARGET **", (320, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255))
                self.debug(img)
            return None


    def selectObject_mean(self):
        centers = []
        img_color, img_mask = self.getBinImage("RED")
        img_show = self.getImage()
        img_show = self.getImage()
        img_show = self.getImage()

        self.debug(img_show)
        # 등고선 따기
        contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if area > 10:
                # cv2.rectangle(img_color, (x, y), (x + w, h + y), (0, 0, 255), 2)
                # 무게중심
                self.Cx = x + w // 2
                self.Cy = y + h // 2
                # bcv2.line(img_color, (self.Cx, self.Cy), (self.Cx, self.Cy), (0, 0, 255), 10)
                # 같은 색상이라도 무게중심의 y값이 큰것일 수록 더 가까이 있음
                centers.append([x, y, w, h])
        print("center1: ", centers)
        if centers:
            centers = sorted(centers, key=lambda x: x[1] + x[3] // 2, reverse=True)[0]
            # 타겟인 영역만큼 그림그리기
            col, row, width, height = centers[0], centers[1], centers[2], centers[3]
            trackWindow = (col, row, width, height)  # 추적할 객체
            roi = img_color[row:row + height, col:col + width]
            roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            roi_hist = cv2.calcHist([roi], [0], None, [180], [0, 180])
            cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
            termination = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
            print("center2: ", centers)
            return img_color, trackWindow, roi_hist, termination
        else:
            return None, None, None, None



    def meanShiftTracking_color(self, img_color, trackWindow, roi_hist, termination,  debug=False):  # 추적할 대상이 정해지면 그 좌표기준으로 사각형을 그려서 추적대상을 잡는다
        need_to_update = True
        ######################## target의 업데이트 ####################
        img_color, trackWindow, roi_hist, termination = self.selectObject_mean()

        if trackWindow is None:
            need_to_update = False

        if trackWindow is not None:
            hsv = cv2.cvtColor(img_color, cv2.COLOR_BGR2HSV)
            dst = cv2.calcBackProject([hsv], [0], roi_hist, [0, 180], 1)  # roi_hist 설정하기
            ret, trackWindow = cv2.meanShift(dst, trackWindow, termination)
            x, y, w, h = trackWindow
            Cx = x + w // 2
            Cy = y + h // 2

        if (debug):
            result = img_color.copy()
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.line(result, (Cx, Cy), (Cx, Cy), (0, 0, 255), 10)
            self.debug(result)

        if Cx < 10 or Cx > img_color.shape[1] - 10 or Cy < 10 or Cy > img_color.shape[0] - 10:
            print("객체가 벗어났습니다.")
            need_to_update = False  # 새로운 객체를 찾으라는 명령을 내린다

        return need_to_update



    def setting_middle(): # 중앙으로 중심을 맞춘다
        pass




if __name__ == "__main__":
    from Sensing.CameraSensor import Camera
    cam = Camera(1)
    imageProcessor = ImageProcessor(cam.width, cam.height)
    cam_t = Thread(target=cam.produce, args=(imageProcessor,))  # 카메라 센싱 쓰레드
    cam_t.start()  # 카메라 프레임 공급 쓰레드 동작

    while(True):
        i = imageProcessor.getBinImage(color="RED1", debug=DEBUG)
    pass
