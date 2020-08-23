from Sensing.CameraSensor import Camera
from Sensing.ImageProcessing import ImageProcessor, Target
from Actuating.Motion import Motion, MOTION
from threading import Thread
import re
import cv2
import time

baseline = (bx, by) = (320, 420)
footline = (fx, fy) = (320, 420)

class Location:
    def __init__(self):
        self.direction = ""
        self.grabMode = None
        self.citizen = 0
        self.target_SIDE = None
        self.walkCount = 0 # 남은 걸음수 담아놓기

    def angle_To_Distance(self, angle):
        angle_walk = {"30": 1, "45": 4, "60": 8, "80": 14, "90": 14}
        walkCount = angle_walk[angle]
        return walkCount

    def distance_To_angle(self, distance): # 남은 걸음수를 이용해서 각도를 조정한다
        walk_to_angle = {1:"30", 4:"45", 8:"60", 14:"80", 15:"90"}
        angle = walk_to_angle[distance]
        return angle  # 목각도를 도출




class Robot:
    def __init__(self):
        self.cam = Camera(0.1)
        self.imageProcessor = ImageProcessor(self.cam.width, self.cam.height)
        self.cam_t = Thread(target=self.cam.produce, args=(self.imageProcessor,))  # 카메라 센싱 쓰레드
        self.cam_t.start()  # 카메라 프레임 공급 쓰레드 동작
        self.motion = Motion()
        self.location = Location()
        self.motion.init()
        self.total_result = {}
        self.possible = []  # 가능한 방향 선택하기  (left45, 30)
        self.direction = ""
        self.grabMode = None
        self.citizen = 0
        self.avoid_drction = None  # 장애물을 피했던 방향


    ###### 현재 블록의 상태 확인################
    def checkCitizen(self, hDirection=None):
        print("CheckCitizen", hDirection)
        # 목각도를 꺾으면서 사진에 해당하는
        head = ["DOWN80", "DOWN60", "DOWN45", "DOWN30"]  # index = i
        head_LR = ["LEFT45", "LEFT30", "CENTER", "RIGHT30", "RIGHT45"]  # index = j
        if hDirection:
            store_color = ""
            for i in range(0, len(head)-1):  # DOWN30는 버리기! 왜냐면 목적지를 객체로 인식해버릴 수 있음
                # 목각도 움직이고 사진찍어서 분석
                self.motion.head(view=MOTION["VIEW"][head[i]], direction=MOTION["DIR"][hDirection])
                print("!!!!!!!!!!다음 객체 찾기모드!!!!!!!!!", hDirection, head[i])
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
        self.walkCount = self.angle_walk[angle]



    def centralize(self, direction=None, angle=None, debug=True):
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

        # 몸 방향 돌리기 :물건을 집고/ 안집고
        if self.grabMode == "GRAB":  # 1...............물건을 집은 상태에서 목적지로 조정하기
            if "LEFT" in self.direction:
                self.motion.turn(grab=self.grabMode)
            elif "RIGHT" in self.direction:
                self.motion.turn(grab=self.grabMode, grab_direction=MOTION["GRAB_TURN"]["RIGHT"],
                                 direct=MOTION["DIR"]["RIGHT"])
            print("centralize/ 집은 상태에서 :", self.direction, "쪽으로 몸을 turn")
        else:  # 2...............물건을 집지 않은 상태에서는 좌우로 이동만
            if "LEFT" in self.direction:
                self.motion.move(grab=self.grabMode, repeat=3)
            elif "RIGHT" in self.direction:
                self.motion.move(grab_direction=MOTION["DIR"]["RIGHT_GRAB"], repeat=3)
            print("centralize/ 안집은 상태에서 :", self.direction, "쪽으로 몸을 turn")

        # 목을 완전히 숙여 걸을 준비 완료
        self.motion.head(view=MOTION["VIEW"]["DOWN18"])
        # self.walking(angle=angle, grab=None)

    def walking(self, angle, grab=None):
        cnt = 0
        while True:

            # <1>.....맵 밖으로 떨어지는지 확인하기
            danger = self.imageProcessor.colorDetected("WHITE")
            if danger:
                # 1......... 위험영역 피하기!
                while danger:
                    if danger == "FRONT":  # 맵 밖의 영역이 시야의 상단에 위치하면 몸을 turn해서 조정
                        self.motion.turn(grab=self.grabMode, direction=self.avoid_drction)
                    else:  # danger = "RIGHT"/"LEFT" 맵 밖의 영역이 양 옆에 있는거면 좌우로 움직이기
                        self.motion.move(grab=self.grabMode, direct=danger, repeat=2)
                    danger = self.imageProcessor.colorDetected("WHITE")

                # 2......... 위험영역을 벗어나면 다시 목적지를 탐색
                if self.grabMode:  # 물건을 잡은 상태이면 목적지를 탐색
                    pass  # walkCount 다시 update!!
                else:  # 물건을 들고있지 않으면 타겟을 다시 탐색
                    pass


            # <2>.......장애물 확인하기 - 장애물이 발견되면 (파란색, 빨간색)
            img_color, img_mask = self.imageProcessor.getBinImage_two(color_lst=["RED", "BLUE"])
            self.imageProcessor.debug(img_color)
            obstacle_contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_TREE,
                                                   cv2.CHAIN_APPROX_SIMPLE)

            ## .......... 장애물 발견하면 피하기  #여기서 맵 밖인지도 확인해야됨
            if obstacle_contours:
                print("Obstacle is traced!!!!")
                obstacle_lst = sorted(obstacle_contours, key=lambda cc: len(cc))
                x, y, w, h = cv2.boundingRect(obstacle_lst[-1])
                Cx = x + w // 2
                Cy = y + h // 2
                cv2.rectangle(img_color, (x, y), (x + w, h + y), (0, 0, 255), 2)
                print("장애물의 중심점 위치 : Cx = {}, Cy = {}".format(Cx, Cy))

                if 130 < Cy < 430 and 20 < Cx < 600:
                    print("____장애물 피하기", self.avoid_drction, "쪽으로 피합니다_______")
                    if 0 < Cx < self.cam.width // 2:  # 왼쪽으로 장애물이 있으면 오른쯕으로 걷기
                        self.motion.move(grab=self.grabMode, direction="RIGHT", repeat=3)
                        self.avoid_drction = "RIGHT"
                    elif self.cam.width// 2 < Cx < self.cam.width:
                        self.motion.move(grab=self.grabMode, direction="LEFT", repeat=3)
                        self.avoid_drction = "LEFT"
                    elif Cx == self.cam.width// 2:
                        self.motion.move(grab=self.grabMode, direction=self.direction, repeat=3)
                        self.avoid_drction = self.direction

                else:  # 아직은 피하기 이른 경우 짧은 전진
                    self.motion.walk(grab=self.grabMode, scope=MOTION["SCOPE"]["SHORT"])


            ## ........피할 대상이 없는 경우는 걷다가 초록색 발견 여부 확인
            else:
                check_obj = self.imageProcessor.colorDetected("GREEN")
                if check_obj:  # 초록색이 발견되면 중심화 시키기
                    self.greenCentral()
                    if self.grabMode == "GRAB":  # 물건을 집은 상태에서는 목적지니까 두는 모션을
                        print("물건을 내려놓습니다.")
                        self.motion.walk(grab=self.grabMode)
                        self.motion.grab(switch="OFF")
                        self.citizen += 1
                        self.target_SIDE = None
                        self.grabMode = None
                        self.Find_Next_Target()
                    else:  # 물건을 잡지 않은 상태에서는 물건을 잡는 모션을
                        print("물건을 집습니다.")
                        # 1..........물건을 집고
                        while True:
                            check_obj, Cx, Cy = self.imageProcessor.colorDetected_Center("GREEN")
                            if Cy > 250:  # 여기서 집었을때의 조건을 다시 주기
                                self.motion.grab()
                                if self.motion.check_GRAB() >= 110:
                                    self.grabMode = "GRAB"
                                    break
                                else:
                                    self.motion.grab(switch="OFF")
                                    self.motion.walk(scope=MOTION["SCOPE"]["SHORT"])
                            else:
                                self.motion.walk(scope=MOTION["SCOPE"]["SHORT"])
                        # 2..........방향을 다시 설정하고 목적지를 탐색한다
                        self.Foward_To_DSTN()
                        self.Find_Detail_DSTN()
                        # 3..........목적지까지의 거리로 update하기

                else:  # 초록색이 발견되지 않으면 우선 옆에 있는지 확인하고 아닌 경우는 앞으로 전진
                    self.motion.walk(grab=self.grabMode)
                    cnt += 1

                    # 측정된 거리에 도달하면 사이드에 객체가 있는지 확인한다.
                    if cnt == self.walkCount and self.grabMode is None:
                        # 1.....오른쪽, 왼쪽 확인해서 물체있나 확인
                        target_SIDE = self.check_side_Target()
                        if target_SIDE:
                            # 2......객체를 발견하면 고개를 내리고 초록색이 있는 쪽으로 다가가기
                            self.motion.head(view=MOTION["VIEW"]["DOWN30"], direction=MOTION["DIR"]["CENTER"])
                            # 3......발견할때까지 몸돌리기 - add_turn 횟수 센다
                            add_turn = 0  # 추가로 턴한 횟수
                            while True:
                                add_turn += 1
                                self.motion.turn(direct=target_SIDE)
                                check_obj = self.imageProcessor.colorDetected("GREEN")
                                if check_obj:  # 초록색을 발견하면 중앙에 들고 집는 것까지
                                    self.greenCentral()  # 이제 물건을 든 상태임
                                    break

                            # 4......물건을 집고 몸을 목적지방향으로 튼다
                            self.Foward_To_DSTN(turn_cnt=add_turn)  ## 만약 목을 270도로 돌릴 수 있으면 굳이 몸 돌릴 필요없음 물건을 들고 어느정도 목적지 방향으로 몸틀고
                            self.Find_Detail_DSTN()  # 이제 거기서 head_LR로 목적지 탐색 및 몸까지 다 돌림
                        else:
                            self.Find_Next_Target()





            ## 세부 걸음 조정1...........장애물 다 피하고 혹시 몰라 살짝이동
            if self.avoid_drction:
                print("self.avoid_direction : !!!!!!장애물 다 피하고 혹시 몰라 살짝이동!!!!!")
                if self.grabMode == "GRAB":  ### 잡았을때 조금만 걷는거!
                    if self.avoid_drction == "LEFT":
                        self.motion.move(grab=self.grabMode, scope=MOTION["SCOPE"]["SHORT"])
                    elif self.avoid_drction == "RIGHT":
                        self.motion.move(grab=self.grabMode, grab_direction=MOTION["DIR"]["RIGHT_GRAB"],
                                         scope=MOTION["SCOPE"]["SHORT"])
                else:
                    if self.avoid_drction == "LEFT":
                        self.motion.move(scope=MOTION["SCOPE"]["SHORT"])
                    elif self.avoid_drction == "RIGHT":
                        self.motion.move(scope=MOTION["SCOPE"]["SHORT"], direct=MOTION["DIR"]["RIGHT"])
                self.avoid_drction = None


    def greenCentral(self):
        print("_______________Centralize GREEN!!_______________")
        while True:
            check_obj, Cx, Cy = self.imageProcessor.colorDetected_Center("GREEN")
            if check_obj:  # 초록색 물체가 발견되면하는 것
                center_X = self.cam.width // 2
                # 초록색을 중앙화 하기
                if Cx > center_X + 200:  # 오른쪽으로 이동
                    self.motion.move(grab=self.grabMode, direction="RIGHT", scope=MOTION["SCOPE"]["SHORT"])
                elif Cx < center_X - 200:  # 왼쪽으로 이동
                    self.motion.move(grab=self.grabMode, direction="LEFT", scope=MOTION["SCOPE"]["SHORT"])
                elif center_X - 200 < Cx < center_X + 200:  # 왼쪽으로 장애물이 있으면 오른쪽으로 걷기
                    return
            else:
                self.motion.walk(grab=self.grabMode, scope=MOTION["SCOPE"]["SHORT"])

    def check_Side_Target(self):
        print("_______________check_Side_Target______________")
        target_SIDE = None
        head_LR = ["LEFT80", "LEFT60", "RIGHT60", "RIGHT80"]
        while True:
            for LR in head_LR:
                self.motion.head(view=MOTION["VIEW"]["DOWN30"], direction=MOTION["DIR"][LR])
                check_obj = self.imageProcessor.colorDetected("GREEN")
                if check_obj:
                    target_SIDE = "LEFT" if "LEFT" in LR else "RIGHT"
                    return target_SIDE
            else:
                self.motion.walk()

    def Foward_To_DSTN(self, turn_cnt=None):
        print("_______________Foward_To_DSTN_______________")
        if self.citizen == 0: # 기존에 돌렸던 방향에서 반대로 돌기!
            if self.target_SIDE == "RIGTH":
                self.motion.turn(grab=self.grabMode, repeat=turn_cnt + 5)
            elif self.target_SIDE == "LEFT":
                self.motion.turn(grab=self.grabMode, grab_direction=MOTION["GRAB_TURN"]["RIGHT"],
                                 repeat=turn_cnt + 7)
        else: # 목적지가 뒤에 있으니까 아예돌아버리기
            if self.target_SIDE == "LEFT":
                self.motion.turn(repeat=turn_cnt + 5)
            else:  # 오른쪽 턴 안잡고
                self.motion.turn(direct=MOTION["DIR"]["RIGHT"], repeat=turn_cnt + 7)

    def Find_Detail_DSTN(self):

        # 0.....이제 남은 거리를 토대로 목각도를 계산해서 and 돌아갈거리 설정
        if self.citizen == 0:  # citizen=0, 목적지거리-객체거리만큼만, citizen>=1 자신이 걸어왔던 거리만큼 돌아가면됨
            self.location.walkCount = 14 - self.location.walkCount
        angle = self.location.distance_To_angle(self.location.walkCount)
        head = "DOWN" + angle  # "30"

        # 1.....이제 목만 좌우로 움직이면서 탐색한다 ← →
        head_LR = ["LEFT90", "LEFT60", "LEFT45", "LEFT30", "CENTER", "RIGHT30", "RIGHT45", "RIGHT60", "RIGHT90"]

        # 2.....목적지가 될 수 있는 면적들을 탐색한다.
        area_lst = []
        for LR in head_LR:
            print("Find_Detail_DSTN    !!!!!!!!방향!!!!!!!!", LR, head)
            self.motion.head(view=MOTION["VIEW"][head], direction=MOTION["DIR"][LR])
            area = self.imageProcessor.colorDetected_Area("GREEN")
            if area:  # 각 라인에 대한 초록색의 위치 데이터를 저장
                area_lst.append((LR, area))

        area_lst = sorted(area_lst, key=lambda x: x[1], reverse=True)
        direction = area_lst[0][0]  # LEFT / RIGHT
        max_area = area_lst[0][1]  # 가장 컸던 면적 = 목적지면적


        # 3......앞서 목적지의 크기라고 생각하는 면적이 나올때까지 돌린다
        while True:
            Area = self.imageProcessor.colorDetected_Area("GREEN")
            if max_area - 300 <= Area <= max_area:  #▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶ 이부분 목적지와 그냥 우유곽이 구분되는 면적 다시 setting
                self.motion.head(view=MOTION["VIEW"]["DOWN18"], direction=MOTION["DIR"]["CENTER"])
                break
            else:
                if "LEFT" in direction:
                    self.motion.turn(grab=self.grabMode)
                elif "RIGHT" in direction:
                    self.motion.turn(grab=self.grabMode, grab_direction=MOTION["GRAB_TURN"]["RIGHT"],
                                     direct=MOTION["DIR"]["RIGHT"])

    def Find_Detail_DSTN_original(self, final=None):
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


    def Find_Next_Target(self):
        print("_________Find_Next_Target__________ 다음 객체탐색")
        self.motion.turn(repeat=6)
        self.motion.head(view=MOTION["VIEW"]["DOWN60"], direction=MOTION["DIR"]["CENTER"])
        # 1....... 다음 객체가 발견될때까지 몸을 돌린다
        while True:
            check_obj = self.imageProcessor.colorDetected("GREEN")
            if check_obj: break
            self.motion.turn(repeat=3)

        # 2....... 해당 객체의 거리를 update 한다
        self.checkCitizen("CENTER")

        # 3....... 오류방지를 위해 목적지 부분을 벗어날때까지 앞으로 전진
        self.motion.head(view=MOTION["VIEW"]["DOWN18"], direction=MOTION["DIR"]["CENTER"])
        while True:
            check_obj = self.imageProcessor.colorDetected("GREEN")
            if check_obj:
                self.motion.walk()







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



if __name__ == "__main__":
    cam = Camera(0.1)
    imageProcessor = ImageProcessor(cam.width, cam.height)
    # p = Process(target=cam.produce, args=[imageProcessor]) # 카메라 센싱 데이터 한 프로세스 내에서 자원의 공유는 가능하다. 그러나 서로 다른 프로세스에서 자원의 공유는 불가능하다....
    # p.start()
    t = Thread(target=cam.produce, args=(imageProcessor,))  # 카메라 센싱 쓰레드
    t.start()

































