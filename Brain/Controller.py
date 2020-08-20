from Sensing.CameraSensor import Camera
from Sensing.ImageProcessing import ImageProcessor, Target
from Actuating.Motion import Motion, MOTION
from threading import Thread
import re
import cv2
import time

baseline = (bx, by) = (320, 420)
footline = (fx, fy) = (320, 420)


class Robot:
    def __init__(self):
        self.cam = Camera(0.1)
        self.imageProcessor = ImageProcessor(self.cam.width, self.cam.height)
        self.cam_t = Thread(target=self.cam.produce, args=(self.imageProcessor,))  # 카메라 센싱 쓰레드
        self.cam_t.start()  # 카메라 프레임 공급 쓰레드 동작
        self.motion = Motion()
        self.motion.init()
        self.j = 0
        self.i = 0
        self.str = ""
        self.total_result = {}
        self.possible = []  # 가능한 방향 선택하기  (left45, 30)
        self.direction = ""
        self.grabMode = None
        self.citizen = 0
        self.turn_direction = ""
        self.angle_walk = {"30": 1, "45": 4, "60": 8, "80": 14, "90": 14}

    ###### 현재 블록의 상태 확인################
    def checkCitizen(self, hDirection=None):
        print("CheckCitizen", hDirection)
        # 목각도를 꺾으면서 사진에 해당하는
        head = ["DOWN80", "DOWN60", "DOWN45", "DOWN30"]  # index = i
        head_LR = ["LEFT45", "LEFT30", "CENTER", "RIGHT30", "RIGHT45"]  # index = j
        if hDirection:
            store_color = ""
            for i in range(len(head)):
                # 목각도 움직이고 사진찍어서 분석
                self.motion.head(view=MOTION["VIEW"][head[i]], direction=MOTION["DIR"][hDirection])
                print("!!!!!!!!!!방향!!!!!!!!", hDirection, head[i])
                print("......")
                result = self.imageProcessor.selectObject_many("alone")  # 반환값 : ["RED", "BLUE", "GREEN"]
                print("......")
                print("......")
                # 각 라인에 대해 분석한 결과를 저장
                store_color += result  # 문자열 결과인 GGRGB 따위를 더해준다
                # 각 라인에 대한 데이터를 저장
                if len(result) != 0:
                    self.total_result[hDirection] = store_color  # {라인: RRGBRRG}
                    angle = re.findall("\d+", head[i])
                    self.possible.append((hDirection, angle[0]))
            print("result:::", self.possible)
            self.possible = sorted(self.possible, key=lambda x: x[1], reverse=True)

        else:
            # 각도를 돌리면서 물체를 확인한다
            for j in range(len(head_LR)):
                store_color = ""
                for i in range(len(head)):
                    # 목각도 움직이고 사진찍어서 분석
                    self.motion.head(view=MOTION["VIEW"][head[i]], direction=MOTION["DIR"][head_LR[j]])
                    print("!!!!!!!!!!방향!!!!!!!!", head_LR[j], head[i])
                    print("......")
                    result = self.imageProcessor.selectObject_many(
                        mode="checkCitizen")  # 반환값 : ["RED", "BLUE", "GREEN"]
                    print("......")
                    print("......")

                    # 각 라인에 대해 분석한 결과를 저장
                    store_color += result  # 문자열 결과인 GGRGB 따위를 더해준다
                    # 각 라인에 대한 데이터를 저장
                    if len(result) != 0:
                        self.total_result[head_LR[j]] = store_color  # {라인: RRGBRRG}
                        angle = re.findall("\d+", head[i])
                        self.possible.append((head_LR[j], angle[0]))
            print("result:::", self.possible)
            self.possible = sorted(self.possible, key=lambda x: x[1])

        self.centralize()  # 해당 방향으로 몸을 돌린다

    def centralize(self, direction=None, angle=None, grab=None, debug=True):
        if direction is not None and angle is not None:
            downAngle = "DOWN" + angle
            self.motion.head(view=MOTION["VIEW"][downAngle])
            self.direction = direction

        if len(self.possible) != 0:
            print(self.possible)
            print("몸을 돌릴 방향", self.possible[0])
            self.direction = self.possible[0][0]
            angle = self.possible[0][1]
            print(self.direction)

        # 걸음수를 담는 변수
        self.walkCount = self.angle_walk[angle]

        # 몸을 완전히 숙인다 발끝이 보이게 그리고 목표물을 향해 조정
        self.motion.head(view=MOTION["VIEW"]["DOWN18"])
        # 몸 방향 돌리기 :물건을 집고/ 안집고
        if self.grabMode == "GRAB":  # 1...............물건을 집은 상태에서 목표물에 조정하기
            if "LEFT" in self.direction:
                self.motion.turn(grab=self.grabMode)
                print("매개변수확인:", grab, "왼쪽으로 몸을 turn")
            elif "RIGHT" in self.direction:
                self.motion.turn(grab=self.grabMode, grab_direction=MOTION["GRAB_TURN"]["RIGHT"],
                                 direct=MOTION["DIR"]["RIGHT"])
                print("매개변수확인:", grab, "오른쪽으로 몸을 turn")
            # self.grabWalking(angle=angle)
        else:  # 2...............물건을 집지 않은 상태에서는 좌우로 이동만
            if "LEFT" in self.direction:
                self.motion.move(grab=self.grabMode, repeat=3)
                print("매개변수확인:", grab, "초기값 조정 : 몸을 왼쪽으로 움직입니다")
            elif "RIGHT" in self.direction:
                self.motion.move(grab_direction=MOTION["DIR"]["RIGHT_GRAB"], repeat=3)
                print("매개변수확인:", grab, "초기값 조정 : 몸을 오른쪽으로 움직입니다")
            self.walking(angle=angle, grab=None)

    # 초록색 대상을 센터화해서 잡기까지
    def greenCentral(self, grab=None):
        while True:
            print("잡을 물체를 탐색합니다: ")
            img_color, img_mask = self.imageProcessor.getBinImage(color="GREEN")
            contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                                   cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) != 0:  # 초록색 물체가 발견되면하는 것
                x, y, w, h = cv2.boundingRect(contours[0])
                Cx = x + w // 2
                Cy = y + h // 2
                center_X = img_color.shape[1] // 2
                area = cv2.contourArea(contours[0])
                # 초록색을 중앙화 하기
                if Cx > center_X + 200:
                    self.motion.move(grab=self.grabMode, grab_direction=MOTION["DIR"]["RIGHT_GRAB"],
                                     direct=MOTION["DIR"]["RIGHT"])
                elif Cx < center_X - 200:
                    self.motion.move(grab=self.grabMode)

                elif center_X - 200 < Cx < center_X + 200:  # 왼쪽으로 장애물이 있으면 오른쯕으로 걷기
                    if grab == "GRAB":  # 물건을 잡은 상태에서는 내려놓기
                        print("물건을 내려놓습니다.")
                        self.motion.walk(walk_signal=MOTION["WALK"]["GRAB"])
                        self.motion.walk(walk_signal=MOTION["WALK"]["GRAB"])
                        self.motion.walk(walk_signal=MOTION["WALK"]["GRAB"])
                        self.motion.walk(walk_signal=MOTION["WALK"]["GRAB"])
                        self.motion.grab_off()
                        self.citizen += 1
                        self.turn_direction = ""
                        self.grabMode = None
                        self.turnMoving()
                        return
                    else:  # 물건을 안잡은 상태를 물건잡기
                        print("물건을 집습니다.")
                        while True:
                            img_color, img_mask = self.imageProcessor.getBinImage(color="GREEN")
                            contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                                                   cv2.CHAIN_APPROX_SIMPLE)
                            print("Cy", Cy)
                            if Cy > 250:  # 여기서 집었을때의 조건을 다시 주기
                                self.motion.grab()
                                if self.motion.check_GRAB() >= 110:
                                    self.grabMode = "GRAB"
                                    print("잡은상태")
                                    return
                                else:
                                    print("놓쳤습니다!!!!!")
                                    self.motion.init()
                                    self.motion.walk(walk_signal=MOTION["WALK"]["SHORT"])
                                    break
                            else:
                                self.motion.walk(walk_signal=MOTION["WALK"]["SHORT"])
                                break


            else:
                self.motion.walk(walk_signal=MOTION["WALK"]["SHORT"])

    def walking(self, angle, grab=None):
        self.motion.head(view=MOTION["VIEW"]["DOWN18"])

        # 목각도와 걸음수 dic

        little = ""
        cnt = 0
        # 첫 걸음을 내딛을때 그린이 아니면 안보일때까지 옆걸음
        while (True):
            obstacle_lst = []
            avoid = False
            color_lst = ["RED", "BLUE"]
            for color in color_lst:
                img_color, img_mask = self.imageProcessor.getBinImage(color=color)
                self.imageProcessor.debug(img_color)
                contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                                       cv2.CHAIN_APPROX_SIMPLE)

                if len(contours) != 0:  # 장애물이 발견되면 (파란색, 빨간색)
                    print(color, " is traced!!!!")
                    obstacle_lst = sorted(contours, key=lambda cc: len(cc))
                    avoid = True
                    color_name = color
                    break

            if avoid:
                x, y, w, h = cv2.boundingRect(obstacle_lst[-1])
                while True:
                    print(color_name, "의 물체를 피합니다")
                    img_color, img_mask = self.imageProcessor.getBinImage(color=color_name)
                    contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                                           cv2.CHAIN_APPROX_SIMPLE)

                    # 다 피해서 나가는 경우는 그냥 나가지 말고 조금이라도 걷고 나가기
                    if len(contours) == 0:
                        if self.grabMode == "GRAB":  ### 잡았을때 조금만 걷는거!
                            if little == "LEFT":
                                print("임시:: 잡고 왼쪽으로 살짝이동")
                                self.motion.move(grab=self.grabMode, scope=MOTION["SCOPE"]["SHORT"])
                            elif little == "RIGHT":
                                print("임시:: 잡고 오른쪽으로 살짝이동")
                                self.motion.move(grab=self.grabMode, grab_direction=MOTION["DIR"]["RIGHT_GRAB"],
                                                 scope=MOTION["SCOPE"]["SHORT"])
                        else:
                            if little == "LEFT":
                                self.motion.move(scope=MOTION["SCOPE"]["SHORT"])
                            elif little == "RIGHT":
                                self.motion.move(scope=MOTION["SCOPE"]["SHORT"], direct=MOTION["DIR"]["RIGHT"])

                        break

                    # 장애물 중심화시키기
                    obstacle_lst = sorted(contours, key=lambda cc: len(cc))
                    x, y, w, h = cv2.boundingRect(obstacle_lst[-1])
                    Cx = x + w // 2
                    Cy = y + h // 2
                    cv2.rectangle(img_color, (x, y), (x + w, h + y), (0, 0, 255), 2)
                    self.imageProcessor.debug(img_color)
                    print("장애물의 중심점 위치 : Cx = {}, Cy = {}".format(Cx, Cy))
                    if 130 < Cy < 430 and 20 < Cx < 600:
                        if 0 < Cx < img_color.shape[1] // 2:  # 왼쪽으로 장애물이 있으면 오른쯕으로 걷기
                            self.motion.move(grab=self.grabMode, grab_direction=MOTION["DIR"]["RIGHT_GRAB"],
                                             direct=MOTION["DIR"]["RIGHT"], repeat=2)
                            little = "RIGHT"
                        elif (img_color.shape[1] // 2) < Cx < img_color.shape[1]:
                            self.motion.move(grab=self.grabMode, repeat=3)
                            little = "LEFT"
                        elif Cx == img_color.shape[1] // 2:
                            if self.direction == "LEFT":
                                self.motion.move(grab=self.grabMode, repeat=3)
                                little = "LEFT"
                            else:
                                self.motion.move(grab=self.grabMode, grab_direction=MOTION["DIR"]["RIGHT_GRAB"],
                                                 direct=MOTION["DIR"]["RIGHT"], repeat=2)
                                little = "RIGHT"
                        print("피하기 mode!", self.grabMode, little, "쪽으로 피합니다")
                    else:  # 아직은 피하기 이른 경우 짧은 전진
                        if self.grabMode == "GRAB":
                            self.motion.walk(walk_signal=MOTION["WALK"]["GRAB"])
                        else:
                            self.motion.walk(walk_signal=MOTION["WALK"]["SHORT"])


            # ........피할 대상이 없는 경우는 걷다가 초록색 발견 여부 확인
            else:
                ############## 걷고 이미지를 받아들인다 #################
                if self.grabMode == "GRAB":
                    self.motion.walk(walk_signal=MOTION["WALK"]["GRAB"])
                else:
                    self.motion.walk()
                cnt += 1
                time.sleep(0.1)
                img_color, img_mask = self.imageProcessor.getBinImage(color="GREEN")
                contours, hierarch = cv2.findContours(img_mask, cv2.RETR_TREE,
                                                      cv2.CHAIN_APPROX_SIMPLE)

                ############ 걷다가 초록색을 발견했을때  - 물건을 잡은 상태 : 물건을 놓기################
                if self.grabMode == "GRAB":
                    if len(contours) != 0:  # 목적지를 발견한것
                        self.greenCentral(self.grabMode)

                    if cnt == self.walkCount:  # 목적지라고 알려진 방향을 갔는데 아직 목적지가 안나옴 다시 세팅
                        self.checkDestination("FINAL")
                        self.centralize(grab="GRAB")  # 잡은 상태에서 해당 방향으로 몸을 돌린다

                ########## 걷다가 초록색을 발견했을때  - 물건을 집지 않은 상태 :물건을 들기 ################
                else:
                    turn_cnt = 0
                    if len(contours) != 0:
                        print("초록색 물건으로 진입합니")
                        self.greenCentral()  # 초록색을 드는것 까지
                        self.forwardToDestination(turn_cnt)
                    if cnt == self.walkCount:  # 일정 거리가 되면 옆에 있는 초록색을 탐색

                        while True:  # 목을 좌우로 돌려 초록색이 있나 확인하기
                            # 1.....오른쪽확인
                            self.motion.head(view=MOTION["VIEW"]["DOWN30"], direction=MOTION["DIR"]["RIGHT60"])
                            img_color, img_mask = self.imageProcessor.getBinImage(color="GREEN")
                            contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                                                   cv2.CHAIN_APPROX_SIMPLE)
                            if len(contours) != 0:
                                self.motion.turn(direct=MOTION["DIR"]["RIGHT"], repeat=5)
                                self.turn_direction = "RIGTH"
                                print("오른쪽발견!!")
                                break

                            else:
                                # 2..... 왼쪽확인
                                self.motion.head(view=MOTION["VIEW"]["DOWN30"], direction=MOTION["DIR"]["LEFT60"])
                                img_color, img_mask = self.imageProcessor.getBinImage(color="GREEN")
                                contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                                                       cv2.CHAIN_APPROX_SIMPLE)
                                if len(contours) != 0:
                                    print("왼쪽발견!!")
                                    self.motion.turn(repeat=5)
                                    self.turn_direction = "LEFT"
                                    break
                                else:
                                    self.motion.walk()

                        self.motion.head(view=MOTION["VIEW"]["DOWN30"], direction=MOTION["DIR"]["CENTER"])
                        while True:
                            if self.turn_direction == "LEFT":  # 왼쪽으로 피했다는건 오른쪽에 장애물이!
                                self.motion.turn()
                            else:  # 오른쪽 턴 안잡고
                                self.motion.turn(direct=MOTION["DIR"]["RIGHT"])
                            turn_cnt += 1
                            print("turn_cnt = ", turn_cnt)
                            img_color, img_mask = self.imageProcessor.getBinImage(color="GREEN")
                            contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                                                   cv2.CHAIN_APPROX_SIMPLE)
                            self.imageProcessor.debug(img_color)
                            if len(contours) != 0:  # 초록색을 발견하면 중앙에 들고 집는 것까지
                                last_turn = little
                                self.motion.walk()
                                self.greenCentral()  # 이제 물건을 든 상태임
                                self.forwardToDestination(0)
                                break

                        #### 이제 목적지로 몸을 돌리는 과정 ######
                        self.centralize(grab="GRAB")  # 잡은 상태에서 해당 방향으로 몸을 돌린다

                if self.imageProcessor.colorDetected("WHITE"):
                    while self.imageProcessor.checkDNGR_ZONE("WHITE"):
                        if little == "LEFT":
                            print("danger Zone!:: LEFT")
                            self.motion.turn(grab=self.grabMode, grab_direction=MOTION["GRAB_TURN"]["RIGHT"])
                        else:
                            print("danger Zone!:: RIGHT")
                            self.motion.turn(grab=self.grabMode)

                    if little == "LEFT":
                        self.motion.move(grab=self.grabMode, grab_direction=MOTION["DIR"]["RIGHT_GRAB"],
                                         direct=MOTION["DIR"]["RIGHT"], repeat=3)

                    else:
                        self.motion.move(grab=self.grabMode, repeat=3)

                    # self.checkCitizen("CENTER")

    def debuggingMode(self, direction, angle):
        self.motion.init()
        targetAngle = "DOWN" + angle
        self.motion.head(view=MOTION["VIEW"][targetAngle], direction=MOTION["DIR"][direction])
        color_lst = ["WHITE"]
        while True:
            for color in color_lst:
                img_color, img_mask = self.imageProcessor.getBinImage(color=color)
                contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                                       cv2.CHAIN_APPROX_SIMPLE)

                if len(contours) == 0: break
                obstacle_lst = sorted(contours, key=lambda cc: len(cc))
                x, y, w, h = cv2.boundingRect(obstacle_lst[-1])
                Cx = x + w // 2
                Cy = y + h // 2
                cv2.line(img_color, (x, y), (x, y), (255, 0, 0), 1)
                cv2.rectangle(img_color, (x, y), (x + w, h + y), (0, 0, 255), 2)
                area = cv2.contourArea(obstacle_lst[-1])
                print("danger!!", self.imageProcessor.checkDNGR_ZONE)
                print("넓이={},높이={}=> (cx={}, cy={})".format(img_color.shape[1], img_color.shape[0], Cx, Cy),
                      "면적은", area / 306081 * 100)
                self.imageProcessor.debug(img_color)

    def forwardToDestination(self, turn_cnt=None):
        ###### 처음으로 물건을 집었으면 몸을 돌리는 과정!! ##########
        ############## 물채를 집고나서 다시 목적지를 확인하는 방법 ################
        print("forwardToDestination")
        if self.citizen >= 1:  # 구한 사람이 1명이상이면 되돌아가기
            # 다시 돌았던 방향의 반대 방향으로 돌기
            self.motion.turn(grab=self.grabMode, repeat=10)
            if self.turn_direction == "LEFT":
                print("한명이상 구출중: 집고서 다시 턴한다", "LEFT")
                self.motion.turn(grab=self.grabMode, repeat=turn_cnt + 5)
            else:
                print("한명이상 구출중: 집고서 다시 턴한다", "RIGTH")
                self.motion.turn(grab=self.grabMode, grab_direction=MOTION["GRAB_TURN"]["RIGHT"],
                                 repeat=turn_cnt + 8)

        elif self.citizen == 0:  # 구한 사람이 0명이면 그냥 정해진대로
            if self.turn_direction == "RIGTH":  # 기존에 돌렸던 방향이
                self.motion.turn(grab=self.grabMode, repeat=turn_cnt + 5)
                print("0명 객체를 집고서 다시 턴한다", self.grabMode, "LEFT")

            elif self.turn_direction == "LEFT":
                self.motion.turn(grab=self.grabMode, grab_direction=MOTION["GRAB_TURN"]["RIGHT"],
                                 repeat=turn_cnt + 7)
                print("0명 객체를 집고서 다시 턴한다", self.grabMode, "RIGTH")
        # 구한사람이 0명일때는 직진
        ##### 목적지를 탐색할때 못 발견하면 몸을 틀어서 확인한다 - 반대로 틀어야됨 #####
        print("forwardToDestination --- 목적지를 탐색합니다")
        self.possible = []
        self.checkDestination()
        while len(self.possible) == 0:
            print("forwardToDestination을 다시!!!")
            if "LEFT" in self.direction:
                self.motion.turn(grab=self.grabMode, grab_direction=MOTION["DIR"]["RIGHT_GRAB"], repeat=2)
            else:
                self.motion.turn(grab=self.grabMode, repeat=2)
            self.checkDestination()
        self.centralize()
        self.motion.head(view=MOTION["VIEW"]["DOWN18"], direction=MOTION["DIR"]["CENTER"])

    def checkDestination(self, final=None):
        print("checkDestination", final)
        # 목각도를 꺾으면서 사진에 해당하는
        if final == "FINAL":
            head = ["DOWN18", "DOWN30", "DOWN45"]
        else:
            head = ["DOWN90", "DOWN80", "DOWN60"]  # index = i

        if "LEFT" in self.direction:
            head_LR = ["CENTER", "RIGHT30", "RIGHT45"]  # index = j
        elif "RIGHT" in self.direction:
            head_LR = ["LEFT45", "LEFT30", "CENTER"]  # index = j
        else:
            head_LR = ["LEFT45", "LEFT30", "CENTER", "RIGHT30", "RIGHT45"]

        # 각도를 돌리면서 물체를 확인한다
        for j in range(len(head_LR)):
            line_area = []
            for i in range(len(head)):
                # 목각도 움직이고 사진찍어서 분석
                self.motion.head(view=MOTION["VIEW"][head[i]], direction=MOTION["DIR"][head_LR[j]])
                print("!!!!!!!!!!방향!!!!!!!!", head_LR[j], head[i])
                print("......")
                area_lst = self.imageProcessor.selectObject_many(mode="destination")  # 반환값 : ["RED", "BLUE", "GREEN"]
                print("......")
                # 각 라인에 대한 초록색의 위치 데이터를 저장
                if len(area_lst) != 0:
                    angle = re.findall("\d+", head[i])
                    self.possible.append((head_LR[j], angle[0], max(area_lst)))

        print("destination::", self.possible)
        # 우선순위 1. 거리가 가장 멀고
        self.possible = sorted(self.possible, key=lambda x: x[1], reverse=True)

        # 우선순위 2. 같은 거리일 경우는 최대 영역순으로 재정렬한다
        max_angle = self.possible[0][1]  # 가장 먼 거리의 angle값
        max_possible_lst = []
        for poss in self.possible:
            if poss[1] == max_angle:
                max_possible_lst.append(poss)
        self.possible = max_possible_lst
        self.possible = sorted(self.possible, key=lambda x: x[2], reverse=True)  # 가장 면적이 큰 순서로 정렬한다
        print("가장큰 각도들과 크기순서로!!", self.possible)

    def turnMoving(self):
        print("turnMoveing ----- 객체 재탐색")
        self.motion.init()
        self.motion.turn(repeat=6)
        self.motion.head(view=MOTION["VIEW"]["DOWN60"], direction=MOTION["DIR"]["CENTER"])

        while True:
            img_color, img_mask = self.imageProcessor.getBinImage("GREEN")
            contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                                   cv2.CHAIN_APPROX_SIMPLE)
            # 초록색이 보일때까지 몸을 돌린다
            if len(contours) == 0:
                self.motion.turn(repeat=3)
            else:
                self.checkCitizen("CENTER")

        self.motion.head(view=MOTION["VIEW"]["DOWN18"], direction=MOTION["DIR"]["CENTER"])
        while True:
            if self.imageProcessor.colorDetected("GREEN"):
                self.motion.walk()
            else:
                break


if __name__ == "__main__":
    cam = Camera(0.1)
    imageProcessor = ImageProcessor(cam.width, cam.height)
    # p = Process(target=cam.produce, args=[imageProcessor]) # 카메라 센싱 데이터 한 프로세스 내에서 자원의 공유는 가능하다. 그러나 서로 다른 프로세스에서 자원의 공유는 불가능하다....
    # p.start()
    t = Thread(target=cam.produce, args=(imageProcessor,))  # 카메라 센싱 쓰레드
    t.start()

































