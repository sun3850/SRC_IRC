from Sensing.CameraSensor import Camera
from Sensing.ImageProcessing import ImageProcessor, Target
from Actuating.Motion import Motion, MOTION
from threading import Thread

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
        self.cam_t = Thread(target=self.cam.produce, args=(self.imageProcessor,)) #카메라 센싱 쓰레드
        self.cam_t.start() # 카메라 프레임 공급 쓰레드 동작
        self.motion = Motion()

    def traceTarget(self):
        VIEW = ["DOWN60", "DOWN45", "DOWN35", "DOWN30", "DOWN10"]
        idx = 0
        self.motion.init()
        while(True):
            print("here1")
            target = self.imageProcessor.findTarget(color="RED", debug=True)
            print("here2")
            if not target :
                continue
            (dx, dy) = target.getDistance(baseline=baseline)
            print("distance gap . dx : {} , dy : {}".format(dx, dy))
            if (-30 < dx < 30 and dy > 0 ):
                print("walk")
                self.motion.walk()
                
            elif ( dx < -40 and dy > 0) : # 오른쪽
                self.motion.move(direct=MOTION["DIR"]["RIGHT"])
                
            elif ( dx > 40 and dy > 0) : # 왼쪽
                self.motion.move(direct=MOTION["DIR"]["LEFT"])
            elif ( dy < 0 ) :
                self.motion.head(view=MOTION["VIEW"][VIEW[idx]])
                idx += 1
                print("head down")
            if idx == len(VIEW):
                return

    def changeAngle(self):
        # 목각도를 변경하기위해 로봇에게 통신을 한다음 다시 track을 시작한다
        print("need to change Angle!")
        self.motion.walk(walk_signal=MOTION["WALK"]["END"])  # 로봇의 전진을 끝내는거
        head = ["DOWN80", "DOWN60", "DOWN45", "DOWN35", "DOWN30", "DOWN10"]   # index = i
        head_LR = ["CENTER", "LEFT30", "LEFT45", "LEFT60", "RIGHT30", "RIGHT45", "RIGHT60"]  # index = j
        i, j = 0, 0
        while i < len(head):
            #for j in range(len(head_LR)):
                #print(head[i], head_LR[j])
            self.motion.head(view=MOTION["MODE"][head[i]])
            img_color, trackWindow, roi_hist, termination = self.imageProcessor.selectObject_mean()
            self.imageProcessor.meanShiftTracking_color(img_color, trackWindow, roi_hist, termination)  # 다시 물체를 탐색한다
            i += 1

    def mean_tracking(self):
        cnt = 0
        img_color, trackWindow, roi_hist, termination = self.imageProcessor.selectObject_mean()
        while True:
            if cnt == 20:
                img_color, trackWindow, roi_hist, termination = self.imageProcessor.selectObject_mean()

            # 만약 추적되는 객체가 없으면 False 를 반환한다
            need_to_change = self.imageProcessor.meanShiftTracking_color(img_color, trackWindow, roi_hist, termination)
            cnt += 1
            if need_to_change is False:
                self.changeAngle()




    # find 찾는거 trace 쫓는거
    ## 라인트레이싱 관련 판단 함수
    # def findYellowLine(self):
    #     while not self.imageProcessor.isYellowLine():
    #         self.motion.head
    #         time.sleep(0.3)
    #     pass
    # def isCorner(self): pass  # 코너점인지 확인
    # def traceYellowLine(self): pass
    # def walkingThroughYellowLine(self): pass

    # ** 임소경 대비 코드들 **
    # ## 코너부분 관련 판단 함수
    # def isCorner(self): pass # 코너점인지 확인
    # def detectRoom(self): pass #
    # def isForkedRoad(self): pass # 갈림길인지 확인
    # def isFinished(self): pass
    # def deciseRegion(self): pass # 감염지역인지, 클린지역인지 판단

    # ## 시민 옮기기
    # def detectCivil(self): pass
    # def traceCivil(self): pass
    # def grabCivil(self): pass
    # def move2Region(self): pass
    # def putCivil(self): pass
    #
    # ## 확진지역에서 옮기기 관련 함수
    # def move2Clean(self): pass

if __name__ == "__main__":
    cam = Camera(0.1)
    imageProcessor = ImageProcessor(cam.width, cam.height)
    # p = Process(target=cam.produce, args=[imageProcessor]) # 카메라 센싱 데이터 한 프로세스 내에서 자원의 공유는 가능하다. 그러나 서로 다른 프로세스에서 자원의 공유는 불가능하다....
    # p.start()
    t = Thread(target=cam.produce, args=(imageProcessor,)) # 카메라 센싱 쓰레드
    t.start()

