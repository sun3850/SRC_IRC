from Sensing.CameraSensor import Camera
from Sensing.ImageProcessing import ImageProcessor, Target
from Actuating.Motion import Motion, MOTION
from threading import Thread

baseline = (bx, by) = (320, 420)
footline = (fx, fy) = (320, 420)

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
        self.cam_t = Thread(target=self.cam.produce, args=(self.imageProcessor,)) #카메라 센싱 쓰레드
        self.cam_t.start() # 카메라 프레임 공급 쓰레드 동작
        self.motion = Motion()
        self.motion.init()
        self.j = 0
        self.i = 0
        self.str = ""


    def traceTarget(self):
        VIEWS = ["DOWN60", "DOWN45", "DOWN35", "DOWN30", "DOWN10"]
        idx = 0
        self.motion.init()
        while(True):
            print("**traceTarget**")
            target = self.imageProcessor.detectTarget(color="RED", debug=True)
            if target is None: # 만약에 객체가 없거나 이탈하면, 다시 객체를 찾아야한다.
                print("**No Target**")
                VIEW = self.findTarget(color="RED", turn="LEFT", debug=True)
                idx = VIEWS.index(VIEW)
                continue
            (dx, dy) = target.getDistance(baseline=baseline)
            print("distance gap . dx : {} , dy : {}".format(dx, dy))
            if(dy > 10): # 기준선 보다 위에 있다면
                if (-40 <= dx <= 40):
                    print("walk")
                    self.motion.walk()
                elif(dx < -40 ): # 른쪽
                    self.motion.move(direct=MOTION["DIR"]["RIGHT"])
                elif(dx > 40 ) : # 왼쪽
                    self.motion.move(direct=MOTION["DIR"]["LEFT"])
            elif ( dy <= 10 ) :
                if idx < len(VIEWS)-1: # 대가리를 다 내린게 아닌데 기준선보다 아래이면
                    self.motion.head(view=MOTION["VIEW"][VIEWS[idx]])
                    idx += 1
                    idx = idx%len(VIEWS)#인덱스 초과시
                    print("head down")
                elif idx == len(VIEWS)-1: # 대가리를 다 내린 상태에서 기준선 보다 아래이면 잡기 시전
                    print("catch: Target, doing grab")
                    self.motion.grab()


    def findTarget(self, color="RED", turn="LEFT", debug=False): # 타깃이 발견될때까지 대가리 상하 좌우 & 몸 틀기 시전
        VIEWS = ["DOWN60", "DOWN45", "DOWN35", "DOWN30", "DOWN10"]
        HEADS = ["CENTER", "LEFT30", "RIGHT30"]
        TURNS = ["LEFT", "RIGHT"]
        HEAD_MOVING = [(VIEW,HEAD) for HEAD in HEADS for VIEW in VIEWS ]

        self.motion.init()

        for VIEW, HEAD in HEAD_MOVING: # 센터 위아래 -> 왼쪽 위아래 -> 오른쪽 위아래 순으로 탐색
            self.motion.head(view=MOTION["VIEW"][VIEW], direction=MOTION["DIR"][HEAD])
            target = self.imageProcessor.detectTarget(color=color, debug=debug)
            if target is None: # 해당 방향에 타깃이 없다면
                continue
            else: # 해당 방향에 타깃이 있다면 , 방향으로 몸을 틀고
                if "LEFT" in VIEW: # 왼쪽에서 발견했으면 왼쪽으로 틀고
                    self.motion.turn(direct=MOTION["DIR"]["LEFT"])
                    self.motion.head(view=MOTION["VIEW"][VIEW]) # 대가리 바로
                    print("find left Target, turn left")
                elif "RIGHT" in VIEW: # 오른쪽에서 발견했으면 오른쪽으로 틀고
                    self.motion.turn(direct=MOTION["DIR"]["RIGHT"]) # 대가리 바로
                    self.motion.head(view=MOTION["VIEW"][VIEW])
                    print("find right Target, turn right")
                else:
                    print("find center Target, not turn")
                return VIEW

        # 모든 탐색을 했지만 아무도 없다면 왼쪽 또는 오른 쪽으로 몸을 틀고 재탐색
        print("cannot find Target, turn "+turn)
        self.motion.turn(direct=MOTION["DIR"][turn])
        return self.findTarget(color=color)








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
        img_color, trackWindow, roi_hist, termination = self.imageProcessor.selectObject_mean()
        # 몸도 움직이기 코드
        if "LEFT" in self.str:
            self.motion.init()
            self.motion.turn()
        else:
            self.motion.init()
            self.motion.turn(direct=MOTION["DIR"]["RIGHT"])
        while True:
            try:

                if cnt % 10 == 10:  # 추적대상 update 하기
                    img_color, trackWindow, roi_hist, termination = self.imageProcessor.selectObject_mean()
                # 만약 추적되는 객체가 없으면 False 를 반환한다
                print("8888")
                print("8888")
                need_to_change = self.imageProcessor.meanShiftTracking_color(img_color, trackWindow, roi_hist, termination)
                cnt += 1
                # 물체를 찾은적이 있으면 움직인다 / 물체를 찾은 적없이 처음 시작하면 무작정 walk 하지 않음
                if cnt == 1:
                    flag = 1
                print("8888")
                print("8888")
                self.motion.walk()
            except:
                if flag == 1:  # 무작정 처음부터 움직이는것 방지하기
                    self.motion.walk()
                    self.motion.walk()
                    self.motion.walk()
                self.j += 1
                self.changeAngle(self.i, self.j)


    def check_color_distance(self):

        # 물체를 찾을 수 있는 각도로 머리를 든다
        self.motion.head(view=MOTION["MODE"]["DOWN80"])

        # 목을 좌우로 움직인다
        head_LR = ["", "CENTER", "LEFT30", "LEFT45", "LEFT60", "RIGHT30", "RIGHT45", "RIGHT60"]  # index = j
        
        head_LR = ["", "CENTER", "LEFT30", "RIGHT30", "LEFT45", "RIGHT45", "LEFT60", "RIGHT60"]  # index = j
        

        cnt = 1
        point_lst = []  # target 색깔이 있는 곳
        while cnt != len(head_LR):
            # 물체를 찾는다
            cnt += 1
            try:
                img_color, trackWindow, roi_hist, termination = self.imageProcessor.selectObject_mean()  # 물체가 있으면 밑에 수행하고 없으면 except를 수행한다
                # 타깃이 확인된 각도를 리스트에 집어넣는다 -> 이값을 이용하여 색깔 인덱스를 기록해야됨
                rr = re.findall("\d+", head_LR[cnt])
                point_lst.append((rr, head_LR[cnt]))
                # [(방향, 각도)] 리스트안에 튜플로 저장해서 각도가 작은것으로 다시 정렬을 한다
                sorted_head_LR = sorted(head_LR, key=lambda x : x[1])
                target = sorted_head_LR[0]
                self.motion.head(target[0])
                self.motion.walk()  # 앞으로 한번만 이동
                self.motion.turn(direct=MOTION["DIR"]["RIGHT"])   # 몸돌리기




            except:
                pass






if __name__ == "__main__":
    cam = Camera(0.1)
    imageProcessor = ImageProcessor(cam.width, cam.height)
    # p = Process(target=cam.produce, args=[imageProcessor]) # 카메라 센싱 데이터 한 프로세스 내에서 자원의 공유는 가능하다. 그러나 서로 다른 프로세스에서 자원의 공유는 불가능하다....
    # p.start()
    t = Thread(target=cam.produce, args=(imageProcessor,)) # 카메라 센싱 쓰레드
    t.start()


