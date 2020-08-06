from Sensing.CameraSensor import Camera
from Sensing.ImageProcessing import *
from Actuating.Motion import Motion, MOTION
from threading import Thread
import re # 숫자랑 문자분리하기

baseline = (bx, by) = (320, 420)


# class Target:
#     def __init__(self):
#         self.mainTarget =
#         self.target =
#     def update(self):
#         self.target

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

    def traceTarget(self):
        VIEW = ["DOWN60", "DOWN45", "DOWN35", "DOWN30", "DOWN10"]
        idx = 0
        self.motion.init()
        while (True):
            print("here1")
            target = self.imageProcessor.detectTarget(color="RED", debug=True)
            if target is None:  # 만약에 객체가 없거나 이탈하면, 다시 객체를 찾아야한다.
                continue
            (dx, dy) = target.getDistance(baseline=baseline)
            print("distance gap . dx : {} , dy : {}".format(dx, dy))
            if (-30 < dx < 30 and dy > 0):
                print("walk")
                self.motion.walk()

            elif (dx < -40 and dy > 0):  # 오른쪽
                self.motion.move(direct=MOTION["DIR"]["RIGHT"])

            elif (dx > 40 and dy > 0):  # 왼쪽
                self.motion.move(direct=MOTION["DIR"]["LEFT"])
            elif (dy < 0):
                self.motion.head(view=MOTION["VIEW"][VIEW[idx]])
                idx += 1
                print("head down")
            if idx == len(VIEW):
                return

    def findTarget(self):  # 타깃이 발견될때까지 대가리 상하 좌우 & 몸 틀기 시전
        VIEW = ["DOWN60", "DOWN45", "DOWN35", "DOWN30", "DOWN10"]
        HEAD = ["LEFT45", "RIGHT45", "CENTER"]

    def changeAngle(self, i, j):
        # 목각도를 변경하기위해 로봇에게 통신을 한다음 다시 track을 시작한다
        #self.motion.walk(walk_signal=MOTION["WALK"]["END"])  # 로봇의 전진을 끝내는거
        head = ["", "DOWN80", "DOWN60", "DOWN45", "DOWN35", "DOWN30", "DOWN10"]  # index = i
        head_LR = ["", "CENTER", "LEFT30", "LEFT45", "LEFT60", "RIGHT30", "RIGHT45", "RIGHT60"]  # index = j
        self.motion.head(view=MOTION["MODE"][head[i]], direction=MOTION["DIR"][head_LR[j]])
        self.str = head_LR[j]
        print(head[i], head_LR[j])
        if self.j == len(head_LR)-1:
            self.j = 0
            self.i += 1
        try:
            self.mean_tracking()
        except:
            print("hello")
            self.changeAngle(self.i, self.j)




    def mean_tracking(self):
        cnt = 0
        flag = 0
        # 처음 target 이미지를 찾는다
        img_color, trackWindow, roi_hist, termination = self.imageProcessor.selectObject_mean(COLORS["RED"])
        # 목의 움직임에 따라 몸도 움직이기 코드
        if "LEFT" in self.str:
            self.motion.init()
            self.motion.turn()
        else:
            self.motion.init()
            self.motion.turn(direct=MOTION["DIR"]["RIGHT"])
        while True:
            try:
                print("8888")
                print("8888")
                # 발견된 물체를 쫓아가는 부분
                self.imageProcessor.meanShiftTracking_color(img_color, trackWindow, roi_hist, termination)
                self.motion.walk()

                # except의 물체를 찾은적이 있으면 움직인다 / 물체를 찾은 적없이 처음 시작하면 무작정 walk 하지 않음
                cnt += 1
                if cnt == 1:
                    flag = 1
                print("8888")
                print("8888")

                # 10프레임당 추적 대상 update 하기
                if cnt % 10 == 10:
                    img_color, trackWindow, roi_hist, termination = self.imageProcessor.selectObject_mean(COLORS["RED"])

            except:
                # 찾은 target 이 없는 경우 -> 일단 앞으로 걸어가서 속도 증진
                if flag == 1:  # 무작정 처음부터 움직이는것 방지하기
                    self.motion.walk()
                    self.motion.walk()
                    self.motion.walk()
                self.j += 1
                self.changeAngle(self.i, self.j)




    # 로봇의 위치를 기록하는 함수
    def check_location(self):

        # 물체를 찾을 수 있는 각도로 머리를 든다
        self.motion.head(view=MOTION["MODE"]["DOWN80"])

        # 목을 좌우로 움직인다-left 로 돌리다가 벽을 마주하면 더 진행하지 말고 Right로 변경한다
        head_LR = ["CENTER", "LEFT30", "LEFT45", "LEFT60", "RIGHT30", "RIGHT45", "RIGHT60"]  # index = j
        head_L = ["LEFT30", "LEFT45", "LEFT60"]
        head_R = ["RIGHT30", "RIGHT45", "RIGHT60"]

        # 우선 초기에는 모든 방향을 다 확인하도록 설정 -> 나중에 변화시킨다
        head_lst = head_LR

        points = []  # target 색이 발견된 위치를 저장한다
        # 물체를 찾을때까지 반복
        cnt = 0
        while True:
            try:
                # 로봇의 움직임 head_LR 머리 좌우만 돌린다
                self.motion.head(direction=MOTION["DIR"][head_lst[cnt]])
                point_motion = head_lst[cnt]
                img = self.imageProcessor.getImage()

                # 벽검사 : 이미지 검사로 해당 방향이 벽인지 확인한다
                if self.imageProcessor.isWall(img):
                    if "LEFT" in point_motion:  # 왼쪽이 벽임
                        head_lst = head_R
                    if "RIGHT" in point_motion:  # 오른쪽이 벽임
                        head_lst = head_L
                    cnt = 0

                # 벽이 아닌 경우 색상 판단 : 이미지를 찾는다 -> 여기서 에러가 발생할 수 있음(try-except처리)
                self.mean_tracking()
                points.append(point_motion)  # 방향과 각도를 집어넣는다 그런다음 각도가 작은 순으로 정렬한다  (각도가 작으면 떨어진 정도가 작기때문에)
                cnt += 1

            except:
                pass

        # # 포인트 점을 다 찾으면 정렬해서 가까운 거리를 추출한다
        # for point in points:
        #         Angle = list(filter(str.isdigit, point_motion))  # 30를 추출한다
        #         Angle = "".join(Angle)




        # point 타깃을 찾고 나서 이제 움직인다
        # # 로봇의 이동
        # self.motion.walk()  # 앞으로 한번만 이동
        # self.motion.turn(direct=MOTION["DIR"]["RIGHT"])   # 몸돌리기







if __name__ == "__main__":
    cam = Camera(0.1)
    imageProcessor = ImageProcessor(cam.width, cam.height)
    # p = Process(target=cam.produce, args=[imageProcessor]) # 카메라 센싱 데이터 한 프로세스 내에서 자원의 공유는 가능하다. 그러나 서로 다른 프로세스에서 자원의 공유는 불가능하다....
    # p.start()
    t = Thread(target=cam.produce, args=(imageProcessor,))  # 카메라 센싱 쓰레드
    t.start()
