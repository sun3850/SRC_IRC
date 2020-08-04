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
        
        W_View_size =  640  #320  #640
        #H_View_size = int(W_View_size / 1.777)
        H_View_size = 480
        self.cap.set(3, W_View_size)
        self.cap.set(4, H_View_size)
        
        self.width = int(self.cap.get(3))
        self.height = int(self.cap.get(4))
        
    def produce(self, consumer):
        while (True):
            ret, frame = self.cap.read()
            # if resource was not produced, do not update ( = consumer cannot get resource )
            if ret is not True:
                continue
            consumer.updateImage(frame)
            time.sleep(0.1)
            # 업데이트 속도 초당 몇 프레임
            

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
