import cv2
import numpy as np
import time
from Motion import *

class TrackTarget():
    def __init__(self):
        self.img = cv2.imread('./img/1.jpg')
        self.cap = cv2.VideoCapture('./img/3.mp4')  # 동영상 사용
        # self.cap = cv2.VideoCapture(0)  # 웹캠 사용하기
        self.centers = []  # 로봇으로부터 가장 가까운 물체일수록 x, y, w, h 순으로 좌표의 값을 담음


        # self.motion = Motion() # 로봇과 통신
        ############################# 색감 지정하기 ############################################
        self.hsv, self.lower_blue1, self.upper_blue1, self.lower_blue2, self.upper_blue2, \
        self.lower_blue3, self.upper_blue3 = self.find_target()
        #####################################################################################

        self.target_x, self.target_y = 0, 0
        self.img_copy = self.img.copy()


        # 로봇의 목각도
        self.neckAngle = 0



        # camshift를 위한 변수
        self.roi_hist = None
        self.trackWindow = None



    #################### 기본적으로 생성시 타깃 색상을 정해주는 메소드 ###########################################
    def find_target(self):  # 단순히 추적할 색상을 정해주는 함수
        hsv, lower_blue1, upper_blue1, lower_blue2, upper_blue2, lower_blue3, upper_blue3 = 0,0,0,0,0,0,0

        # 마우스 왼쪽 버튼 누를시 위치에 있는 픽셀값을 읽어와서 HSV로 변환합니다.
        ### 나중에 여기 수정!!###

        # 컬러를 설정하는 방법1
        color = self.img[192, 391] #[y, x]좌표의 픽셀의 정보의 색상정보를 읽어 hsv로 바꾸기
        # 컬러를 설정하는 방법2
        color = [176, 112,  42]  # 빨간색의 경우
        one_pixel = np.uint8([[color]])
        hsv = cv2.cvtColor(one_pixel, cv2.COLOR_BGR2HSV)
        hsv = hsv[0][0]

        threshold = cv2.getTrackbarPos('threshold', 'img_result')

        # HSV 색공간에서 마우스 클릭으로 얻은 픽셀값과 유사한 필셀값의 범위를 정합니다.
        if hsv[0] < 10:
            lower_blue1 = np.array([hsv[0] - 10 + 180, 30, 30])
            upper_blue1 = np.array([180, 255, 255])
            lower_blue2 = np.array([0, 30, 30])
            upper_blue2 = np.array([hsv[0], 255, 255])
            lower_blue3 = np.array([hsv[0], 30, 30])
            upper_blue3 = np.array([hsv[0] + 10, 255, 255])

        elif hsv[0] > 170:
            lower_blue1 = np.array([hsv[0], 30, 30])
            upper_blue1 = np.array([180, 255, 255])
            lower_blue2 = np.array([0, 30, 30])
            upper_blue2 = np.array([hsv[0] + 10 - 180, 255, 255])
            lower_blue3 = np.array([hsv[0] - 10, 30, 30])
            upper_blue3 = np.array([hsv[0], 255, 255])

        else:
            lower_blue1 = np.array([hsv[0], 30, 30])
            upper_blue1 = np.array([hsv[0] + 10, 255, 255])
            lower_blue2 = np.array([hsv[0] - 10, 30, 30])
            upper_blue2 = np.array([hsv[0], 255, 255])
            lower_blue3 = np.array([hsv[0] - 10, 30, 30])
            upper_blue3 = np.array([hsv[0], 255, 255])
        return hsv, lower_blue1, upper_blue1, lower_blue2, upper_blue2, lower_blue3, upper_blue3


    def changeAngle(self):
        # 목각도를 변경하기위해 로봇에게 통신을 한다음 다시 track을 시작한다
        print("need to change Angle!")
      #  self.motion.walk(MOTION["WALK"]["END"])  # 로봇의 전진을 끝내는거

        # 목각도가 최대한으로 꺾이는 경우 -> 물건을 집는 알고리즘을 호출한다.
        if self.neckAngle != 90:
            self.neckAngle += 30  # 30도씩 숙인다
            self.trackObject2()  # 다시 물체를 탐색한다
        else:  # 최대한으로 꺾이는 순간
            pass  # 물건 집기 알고리즘


    def Rotate(self, src, degrees):  # 이미지 rotation 하기
        if degrees == 90:
            dst = cv2.transpose(src)
            dst = cv2.flip(dst, 1)

        elif degrees == 180:
            dst = cv2.flip(src, -1)

        elif degrees == 270:
            dst = cv2.transpose(src)
            dst = cv2.flip(dst, 0)
        else:
            pass
        return dst


############## 색상을 토대로 객체들의 리스트를 설정하고 -> 파악된 객체중에서 가장 가까운 객체를 설정한다 ############################
    def selectObject(self, img_color=None):
        self.centers = []
        if img_color is None:
            self.cap = cv2.VideoCapture('./img/7.mp4')  # 동영상 사용
            # self.cap = cv2.VideoCapture(0)  # 웹캠 사용하기
            ret, img_color = self.cap.read()
            img_color = self.Rotate(img_color, 90)  # 90 or 180 or 270  이미지 회전하기
        # 원본 영상을 HSV 영상으로 변환합니다.
        img_hsv = cv2.cvtColor(img_color, cv2.COLOR_BGR2HSV)

        # 범위 값으로 HSV 이미지에서 마스크를 생성합니다.
        img_mask1 = cv2.inRange(img_hsv, self.lower_blue1, self.upper_blue1)
        img_mask2 = cv2.inRange(img_hsv, self.lower_blue2, self.upper_blue2)
        img_mask3 = cv2.inRange(img_hsv, self.lower_blue3, self.upper_blue3)
        img_mask = img_mask1 | img_mask2 | img_mask3  # 이진화된 이미지 get

        # 잡음제거
        kernel = np.ones((11, 11), np.uint8)
        img_mask = cv2.morphologyEx(img_mask, cv2.MORPH_OPEN, kernel)
        img_mask = cv2.morphologyEx(img_mask, cv2.MORPH_CLOSE, kernel)

        # 등고선 따기
        contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)


        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if area > 1000:
                #cv2.rectangle(img_color, (x, y), (x + w, h + y), (0, 0, 255), 2)
                # 무게중심
                self.Cx = x + w // 2
                self.Cy = y + h // 2
                #cv2.line(img_color, (self.Cx, self.Cy), (self.Cx, self.Cy), (0, 0, 255), 10)
                # 같은 색상이라도 무게중심의 y값이 큰것일 수록 더 가까이 있음
                self.centers.append([x, y, w, h])
        self.centers = sorted(self.centers, key=lambda x: x[1] + x[3] // 2, reverse=True)
        print('객체의 개수:', len(self.centers))
        #cv2.imshow('select_object', img_color)

    def selectObject3(self, img_color=None):
        self.centers = []
        if img_color is None:
            self.cap = cv2.VideoCapture('./img/7.mp4')  # 동영상 사용
            # self.cap = cv2.VideoCapture(0)  # 웹캠 사용하기
            ret, img_color = self.cap.read()
            img_color = self.Rotate(img_color, 90)  # 90 or 180 or 270  이미지 회전하기
        #원본 영상을 HSV 영상으로 변환합니다.
        img_hsv = cv2.cvtColor(img_color, cv2.COLOR_BGR2HSV)

        # 범위 값으로 HSV 이미지에서 마스크를 생성합니다.
        img_mask1 = cv2.inRange(img_hsv, self.lower_blue1, self.upper_blue1)
        img_mask2 = cv2.inRange(img_hsv, self.lower_blue2, self.upper_blue2)
        img_mask3 = cv2.inRange(img_hsv, self.lower_blue3, self.upper_blue3)
        img_mask = img_mask1 | img_mask2 | img_mask3  # 이진화된 이미지 get

        # 잡음제거
        kernel = np.ones((11, 11), np.uint8)
        img_mask = cv2.morphologyEx(img_mask, cv2.MORPH_OPEN, kernel)
        img_mask = cv2.morphologyEx(img_mask, cv2.MORPH_CLOSE, kernel)

        # 등고선 따기
        contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                               cv2.CHAIN_APPROX_SIMPLE)


        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if area > 1000:
                #cv2.rectangle(img_color, (x, y), (x + w, h + y), (0, 0, 255), 2)
                # 무게중심
                self.Cx = x + w // 2
                self.Cy = y + h // 2
                #cv2.line(img_color, (self.Cx, self.Cy), (self.Cx, self.Cy), (0, 0, 255), 10)
                # 같은 색상이라도 무게중심의 y값이 큰것일 수록 더 가까이 있음
                self.centers.append([x, y, w, h])
        self.centers = sorted(self.centers, key=lambda x: x[1] + x[3] // 2, reverse=True)[0]
        # 타겟인 영역만큼 그림그리기
        col, row, width, height = self.centers[0], self.centers[1], self.centers[2], self.centers[3]
        trackWindow = (col, row, width, height)  # 추적할 객체
        roi = img_color[row:row + height, col:col + width]
        roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        roi_hist = cv2.calcHist([roi], [0], None, [180], [0, 180])
        cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)

        termination = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
        return trackWindow, roi_hist, termination


    # selectObject 를 이용하여 타깃하는 객체를 설정하고  -> camShiftTracking 으로 객체를 다시 추적한다
    def camShiftTracking_color(self):  # 추적할 대상이 정해지면 그 좌표기준으로 사각형을 그려서 추적대상을 잡는다
        cnt = 0
        # 이제 객체를 camshift로 추적한다.
        ret, img_color = self.cap.read()
        img_color = self.Rotate(img_color, 90)  # 90 or 180 or 270
        trackWindow, roi_hist, termination = self.selectObject3(img_color)

        while True:
            ret, img_color = self.cap.read()
            flag = 0
            img_color = self.Rotate(img_color, 90)  # 90 or 180 or 270
            if not ret:
                break
            ######################## target의 업데이트 ####################
            trackWindow, roi_hist, termination = self.selectObject3(img_color)

            if cnt == 20:
                print("update!")
                trackWindow, roi_hist, termination = self.selectObject3(img_color)
                cnt = 0
            #if trackWindow is not None:
            hsv = cv2.cvtColor(img_color, cv2.COLOR_BGR2HSV)
            dst = cv2.calcBackProject([hsv], [0], roi_hist, [0, 180], 1)  # roi_hist 설정하기
            ret, trackWindow = cv2.meanShift(dst, trackWindow, termination)
            x, y, w, h = trackWindow
            cv2.rectangle(img_color, (x, y), (x+w, y+h), (0, 255, 0), 2)
            ########### 만약 무게중심이 화면 밖을 벗어나면 #################
            # center = cv2.moments(ret)
            # Cx = int(center['m10']/center['m00'])
            # Cy = int(center['m01']/center['m00'])
            Cx = x + w // 2
            Cy = y + h // 2
            cv2.line(img_color, (Cx, Cy), (Cx, Cy), (0, 0, 255), 10)
            cnt += 1
            if Cx < 20 or Cx > img_color.shape[1] - 50 or Cy < 20 or Cy > img_color.shape[0] - 50:
                print("진입")
                flag = 1  # 새로운 객체를 찾으라는 명령을 내린다
               # break



            cv2.imshow('camShiftTracking_color', img_color)
            if cv2.waitKey(33) > 0: break

        if flag == 1:
            # 목각도를 회전한다음 물체검색 다시
            print("물체검색을 다시 시작합니다.")
            self.selectObject()

        self.cap.release()
        cv2.destroyAllWindows()

    # selectObject 를 이용하여 타깃하는 객체를 설정하고  -> camShiftTracking 으로 객체를 다시 추적한다
    def camShiftTracking(self, col, row, width, height):  # 추적할 대상이 정해지면 그 좌표기준으로 사각형을 그려서 추적대상을 잡는다
        # 타겟인 객체를 추적하기 위해 세팅하기 - 첫이미지 가져오기
        ret, img_color = self.cap.read()
        img_color = self.Rotate(img_color, 90)  # 90 or 180 or 270

        # 타겟인 영역만큼 그림그리기
        cv2.rectangle(img_color, (col, row), (col + width, row + height), (0, 255, 0), 2)
        trackWindow = (col, row, width, height)  # 추적할 객체
        print(trackWindow)
        roi = img_color[row:row + height, col:col + width]
        roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        roi_hist = cv2.calcHist([roi], [0], None, [180], [0, 180])
        cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)

        termination = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)

        cv2.imshow("chek_cam", img_color)

        # 이제 객체를 camshift로 추적한다.
        while True:
            ret, img_color = self.cap.read()
            flag = 0
            img_color = self.Rotate(img_color, 90)  # 90 or 180 or 270
            if not ret:
                break
            if trackWindow is not None:
                hsv = cv2.cvtColor(img_color, cv2.COLOR_BGR2HSV)
                dst = cv2.calcBackProject([hsv], [0], roi_hist, [0, 180], 1)  # roi_hist 설정하기
                ret, trackWindow = cv2.meanShift(dst, trackWindow, termination)
                x, y, w, h = trackWindow
                cv2.rectangle(img_color, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # ret, trackWindow = cv2.CamShift(dst, trackWindow, termination)
                # pts = cv2.boxPoints(ret)
                # pts = np.int0(pts)
                # cv2.polylines(img_color, [pts], True, (0, 255, 0), 2)
                ########### 만약 무게중심이 화면 밖을 벗어나면 #################
                # center = cv2.moments(ret)
                # Cx = int(center['m10']/center['m00'])
                # Cy = int(center['m01']/center['m00'])
                Cx = x + w // 2
                Cy = y + h // 2
                cv2.line(img_color, (Cx, Cy), (Cx, Cy), (0, 0, 255), 10)

                if Cx < 20 or Cx > img_color.shape[1] - 100 or Cy < 20 or Cy > img_color.shape[0] - 70:
                    print("진입")
                    flag = 1  # 새로운 객체를 찾으라는 명령을 내린다
                    break

            cv2.imshow('frame', img_color)
            if cv2.waitKey(33) > 0: break

        if flag == 1:
            # 목각도를 회전한다음 물체검색 다시
            print("물체검색을 다시 시작합니다.")
            self.selectObject()

        self.cap.release()
        cv2.destroyAllWindows()

    def trackObject(self):  # 여기 callback으로 matchfood 넣을지 고민
        while (True):
            ret, img_color = self.cap.read()
            if not ret:
                break

            img_color = self.Rotate(img_color, 90)  # 90 or 180 or 270
            height, width = img_color.shape[:2]
            # img_color = cv.resize(img_color, (width, height), interpolation=cv.INTER_AREA)

            # 원본 영상을 HSV 영상으로 변환합니다.
            img_hsv = cv2.cvtColor(img_color, cv2.COLOR_BGR2HSV)

            # 범위 값으로 HSV 이미지에서 마스크를 생성합니다.
            img_mask1 = cv2.inRange(img_hsv, self.lower_blue1, self.upper_blue1)
            img_mask2 = cv2.inRange(img_hsv, self.lower_blue2, self.upper_blue2)
            img_mask3 = cv2.inRange(img_hsv, self.lower_blue3, self.upper_blue3)
            img_mask = img_mask1 | img_mask2 | img_mask3  # 이진화된 이미지 get

            # 잡음제거
            kernel = np.ones((11, 11), np.uint8)
            img_mask = cv2.morphologyEx(img_mask, cv2.MORPH_OPEN, kernel)
            img_mask = cv2.morphologyEx(img_mask, cv2.MORPH_CLOSE, kernel)
            img_result = cv2.bitwise_and(img_color, img_color, mask=img_mask)

            # 등고선 따기
            contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_EXTERNAL,
                                                   cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 1000:  # 노이즈를 제거하기 위해 일정 넓이 이상의 물체만 잡는다
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(img_color, (x, y), (x + w, h + y), (0, 0, 255), 2)
                    # 무게중심
                    self.Cx = x + w // 2
                    self.Cy = y + h // 2
                    cv2.line(img_color, (self.Cx, self.Cy), (self.Cx, self.Cy), (0, 0, 255), 10)
                    # 같은 색상이라도 무게중심의 y값이 작은것일 수록 더 가까이 있음
                    # 무게중심이 아래로 내려가서 시야에서 가려지기전에 가려질 듯하면-> 목각도를 내려서 타깃을 확인한다 : 주의 끊기면 안됨 물체추적 끝남
                    if height - 40 <= self.Cy <= height:
                        self.changeAngle()


            ##############################  Track Blue 끝!##############################################
            # 마스크 이미지로 원본 이미지에서 범위값에 해당되는 영상 부분을 획득합니다.
            cv2.imshow('img_color', img_color)
            cv2.imshow('img_result', img_result)  # 트랙바가 생성될 창

            # ESC 키누르면 종료
            if cv2.waitKey(1) & 0xFF == 27:
                break

        cv2.destroyAllWindows()

    def trackObject2(self):  # 색으로 추적하는 것중에 y좌표가 가장 작은 애만 추적
        while (True):
            ret, img_color = self.cap.read()
            if not ret:
                break
            img_color = self.Rotate(img_color, 90)  # 90 or 180 or 270
            self.selectObject(img_color)
            x, y, w, h = self.centers[0][0], self.centers[0][1], self.centers[0][2], self.centers[0][3]
            cv2.rectangle(img_color, (x, y), (x + w, h + y), (0, 0, 255), 2)
            # 무게중심
            self.Cx = x + w // 2
            self.Cy = y + h // 2
            cv2.line(img_color, (self.Cx, self.Cy), (self.Cx, self.Cy), (0, 0, 255), 10)
            # 같은 색상이라도 무게중심의 y값이 작은것일 수록 더 가까이 있음
            # 무게중심이 아래로 내려가서 시야에서 가려지기전에 가려질 듯하면-> 목각도를 내려서 타깃을 확인한다 : 주의 끊기면 안됨 물체추적 끝남
            height, width = img_color.shape[:2]

            if height - 40 <= self.Cy <= height:
                print("물체를 다시 겁색합니다")
                self.changeAngle()
                break


            ##############################  Track Blue 끝!##############################################
            # 마스크 이미지로 원본 이미지에서 범위값에 해당되는 영상 부분을 획득합니다.
            cv2.imshow('img_color', img_color)
           # cv2.imshow('img_result', img_result)  # 트랙바가 생성될 창

            # ESC 키누르면 종료
            if cv2.waitKey(1) & 0xFF == 27:
                break

        cv2.destroyAllWindows()



if __name__ == '__main__':
    trackTarget = TrackTarget()
#    motion = Motion()
    trackTarget.trackObject2()
    trackTarget.camShiftTracking_color()
    while(1):
        trackTarget.selectObject()
        if len(trackTarget.centers) != 0:
            print("물체추적을 시작합니다")
            #motion.walk()  # 타깃을 발견했음 로봇이 움직임 전진
            num = 0
            trackTarget.camShiftTracking(trackTarget.centers[num][0], trackTarget.centers[num][1],
                                     trackTarget.centers[num][2], trackTarget.centers[num][3])   ########## 0번째로 바꿔야됨 그게 제일 가까운거니까
