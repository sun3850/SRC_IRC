import cv2
import time

# import argparse
# import multiprocessing
# from .ImageProcessing import ImageProcessor
CAM_ID = 0


class Camera:
    def __init__(self, fps=0.1):
        self.fps = fps
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.width = 640
        self.height = 480
        self.cap.set(3, self.width)
        self.cap.set(4, self.height)
        self.fourcc = None
        self.out = None

    def produce(self, consumer, record=True, filename="out"):
        if record:
            self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # 녹화기 생성
            self.out = cv2.VideoWriter(str(filename) + ".avi'", self.fourcc, 30.0, (self.width * 2, self.height * 2))

        while (True):
            ret, frame = self.cap.read()
            # if resource was not produced, do not update ( = consumer cannot get resource )
            if ret is not True:
                continue
            consumer.updateImage(frame)
            if record:
                self.out.write(consumer.debug())
            time.sleep(self.fps)
            # 업데이트 속도 초당 몇 프레임

    def __del__(self):
        self.cap.release()
        self.out.release()

#
# if __name__ ==  "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--video', default=0, usage="input filename")
#     parser.add_argument('--buffer', default=4, usage="input filename")
#     args = parser.parse_args()
#     cap = cv2.VideoCapture(args.video)
#     cap.set(cv2.CAP_PROP_BUFFERSIZE, args.buffer)
#
#     width = cap.get(3)
#     height = cap.get(4)
#
#     imageProcessor = ImageProcessor()
#     while(True):
#         ret, frame = cap.read()
#         if ret is not True:
#             continue
#         imageProcessor.updateImage(frame)
