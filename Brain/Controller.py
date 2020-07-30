from Sensing.CameraSensor import Camera
from Sensing.ImageProcessing import ImageProcessor
from Actuating.Motion import Motion
# from multiprocessing import Process
from threading import Thread
import time

class Robot:
    def __init__(self):
        self.cam = Camera(0.1)
        self.imageProcessor = ImageProcessor(cam.width, cam.height)
        self.cam_t = Thread(target=cam.produce, args=(imageProcessor,)) #카메라 센싱 쓰레드
        self.cam_t.start() # 카메라 프레임 공급 쓰레드 동작
        self.motion = Motion()
        self.motion.run() # 모션 시리얼 활성화

    def findTarget(self): pass # 로봇의 행동이 끝나면 다음 타깃을 찾는다.

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
    #
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

