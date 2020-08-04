import cv2
import numpy as np
import time
from Actuating.Motion import *

class TrackTarget():
    def __init__(self):
        # self.cap = cv2.VideoCapture('./img/3.mp4')  # 동영상 사용
        CAM_ID = 0
        W_View_size = 640
        #H_View_size = int(W_View_size / 1.777)
        H_View_size = int(W_View_size / 1.333)

        self.cap = cv2.VideoCapture(CAM_ID)  # 카메라 생성
        self.cap.set(3, 640)
        self.cap.set(4, 480)
        self.centers = []  # 로봇으로부터 가장 가까운 물체일수록 x, y, w, h 순으로 좌표의 값을 담음


        self.motion = Motion() # 로봇과 통신
        ############################# 색감 지정하기 ############################################
        self.hsv, self.lower_blue1, self.upper_blue1, self.lower_blue2, self.upper_blue2, \
        self.lower_blue3, self.upper_blue3 = self.find_target()
        #####################################################################################

        self.target_x, self.target_y = 0, 0



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
        # color = self.img[192, 391] #[y, x]좌표의 픽셀의 정보의 색상정보를 읽어 hsv로 바꾸기
        # 컬러를 설정하는 방법2
        color = [216, 128,  24]  # 빨간색의 경우
        one_pixel = np.uint8([[color]])
        hsv = cv2.cvtColor(one_pixel, cv2.COLOR_BGR2HSV)
        hsv = hsv[0][0]

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




############## 색상을 토대로 객체들의 리스트를 설정하고 -> 파악된 객체중에서 가장 가까운 객체를 설정한다 ############################
    def selectObject(self, img_color=None):
        self.centers = []
        if img_color is None:
            ret, img_color = self.cap.read()
            # img_color = self.Rotate(img_color, 90)  # 90 or 180 or 270  이미지 회전하기
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

        
        if len(contours) == 0:
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
            #cv2.imshow('select_object', img_color)
        else: self.changeAngle()
        



     # selectObject 를 이용하여 타깃하는 객체를 설정하고  -> camShiftTracking 으로 객체를 다시 추적한다







    def trackObject_all(self):  # 색상으로 추적 -> 색만 같으면 여러개의 대상으로 추적 
        while (True):
            #img_color = self.img.copy()

            ret, img_color = self.cap.read()
            if not ret:
                break


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
            max = 0

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




    # def trackObject_one(self):  # 색상으로 추적 -> 같은 색상 중에서  y좌표가 가장 작은 애만 추적  -> 하나만 추적하는것
    #     while (True):
    #         ret, img_color = self.cap.read()
    #         if not ret:
    #             break
    #         self.selectObject(img_color)  # 파란색을 띄는 물체의 사각형 꼭짓점을 받아온다
    #
    #         if len(self.centers) != 0:
    #             x, y, w, h = self.centers[0][0], self.centers[0][1], self.centers[0][2], self.centers[0][3]
    #             cv2.rectangle(img_color, (x, y), (x + w, h + y), (0, 0, 255), 2)
    #             # 무게중심
    #             self.Cx = x + w // 2
    #             self.Cy = y + h // 2
    #             cv2.line(img_color, (self.Cx, self.Cy), (self.Cx, self.Cy), (0, 0, 255), 10)
    #             # 같은 색상이라도 무게중심의 y값이 작은것일 수록 더 가까이 있음
    #             # 무게중심이 아래로 내려가서 시야에서 가려지기전에 가려질 듯하면-> 목각도를 내려서 타깃을 확인한다 : 주의 끊기면 안됨 물체추적 끝남
    #             height, width = img_color.shape[:2]
    #
    #             if height - 40 <= self.Cy <= height:
    #                 print("물체를 다시 겁색합니다")
    #                 self.changeAngle()
    #                 break
    #
    #
    #         ##############################  Track Blue 끝!##############################################
    #         # 마스크 이미지로 원본 이미지에서 범위값에 해당되는 영상 부분을 획득합니다.
    #         cv2.imshow('img_color', img_color)
    #        # cv2.imshow('img_result', img_result)  # 트랙바가 생성될 창
    #
    #         # ESC 키누르면 종료
    #         if cv2.waitKey(1) & 0xFF == 27:
    #             break
    #
    #     cv2.destroyAllWindows()


    


if __name__ == '__main__':
    trackTarget = TrackTarget()
    
    # 로봇 모션의 객체를 생성 
    motion = Motion()
    
    motion.init()

    #trackTarget.trackObject_one()
    trackTarget.camShiftTracking_color()
    while(1):
        trackTarget.selectObject()
        if len(trackTarget.centers) != 0:
            print("물체추적을 시작합니다")
            motion.walk()  # 타깃을 발견했음 로봇이 움직임 전진
            num = 0
            trackTarget.camShiftTracking(trackTarget.centers[num][0], trackTarget.centers[num][1],
                                     trackTarget.centers[num][2], trackTarget.centers[num][3])  
