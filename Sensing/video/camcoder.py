#!/opt/local/bin/python
# -*- coding: utf-8 -*-
import cv2

########### 추가 ##################
import time  # time 라이브러리

###################################

CAM_ID = 0
W_View_size =  640  #320  #640
#H_View_size = int(W_View_size / 1.777)
H_View_size = 480

cam = cv2.VideoCapture(CAM_ID)  # 카메라 생성
cam.set(3, W_View_size)
cam.set(4, H_View_size)

cx = W_View_size//2
cy = H_View_size//2

fourcc = cv2.VideoWriter_fourcc(*'MJPG') # 녹화기 생성
out = cv2.VideoWriter('output.avi', fourcc, 30.0, (int(cam.get(3)),int(cam.get(4))))

# 윈도우 생성 및 사이즈 변경
cv2.namedWindow('CAM_Window')

########### 추가 ##################
prevTime = 0  # 이전 시간을 저장할 변수
###################################
while (cam.isOpened()):

    # 카메라에서 이미지 얻기
        ret, frame = cam.read()
        if ret:
            ########### 추가 ##################
            # 현재 시간 가져오기 (초단위로 가져옴)
            curTime = time.time()
            # 현재 시간에서 이전 시간을 빼면?
            # 한번 돌아온 시간!!

            sec = curTime - prevTime
            # 이전 시간을 현재시간으로 다시 저장시킴
            prevTime = curTime
        
            # 프레임 계산 한바퀴 돌아온 시간을 1초로 나누면 된다.
            # 1 / time per frame
            fps = 1 / (sec)
        
            # # 디버그 메시지로 확인해보기
            # print("Time {0} ".format(sec))
            # print("Estimated fps {0} ".format(fps))
        
            # 프레임 수를 문자열에 저장
            str = "FPS : %0.1f" % fps
            #frame = cv2.flip(frame, 1)
            out.write(frame)
            # 표시
            cv2.putText(frame, str, (0, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0))
            cv2.line(frame, (cx, 0), (cx, H_View_size), (0, 255, 0), 1)
            cv2.line(frame, (0, cy), (W_View_size, cy), (0, 255, 0), 1)
            cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)
            ###################################
            # 얻어온 프레임 녹화
            # 얻어온 이미지 윈도우에 표시
            cv2.imshow('CAM_Window', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            continue
# 윈도우 종료
cam.release()
out.release()
cv2.destroyWindow('CAM_Window')
cv2.destroyAllWindows()
