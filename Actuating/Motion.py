import platform
import numpy as np
import argparse
import cv2
import serial
import time
import sys
from threading import Thread

MOTION = dict()
MOTION["WALK"] = {

}
MOTION["SPEED"] = {

}
MOTION["DIRECTION"] = {

}
MOTION["SCOPE"] = {

}
MOTION["HEAD"] = {

}

class Motion:
    def __init__(self):
        self.serial_use = 1
        self.serial_port = None
        self.Read_RX = 0
        self.receiving_exit = 1
        self.threading_Time = 0.01
        BPS = 4800  # 4800,9600,14400, 19200,28800, 57600, 115200

        # ---------local Serial Port : ttyS0 --------
        # ---------USB Serial Port : ttyAMA0 --------

        self.serial_port = serial.Serial('/dev/ttyS0', BPS, timeout=0.01)
        self.serial_port.flush()  # serial cls
        self.serial_t = Thread(target=self.Receiving, args=(self.serial_port,))
        self.serial_t.daemon = True
        self.serial_t.start()
        time.sleep(0.1)

    def start(self): pass
    def init(self): pass
    def walk(self): pass
    def head(self): pass
    def move(self): pass
    def turn(self): pass
    def grab(self): pass

    def TX_data_py2(self, one_byte):  # one_byte= 0~255

        self.serial_port.write(serial.to_bytes([one_byte]))  # python3
        time.sleep(1)

    def RX_data(self):
        if self.serial_port.inWaiting() > 0:
            result = self.serial_port.read(1)
            RX = ord(result)
            return RX
        else:
            return 0

    def Receiving(self, ser):
        global receiving_exit
        #
        # global X_255_point
        # global Y_255_point
        # global X_Size
        # global Y_Size
        # global Area, Angle

        receiving_exit = 1
        while True:
            if receiving_exit == 0:
                break
            time.sleep(self.threading_Time)
            while ser.inWaiting() > 0:
                result = ser.read(1)
                RX = ord(result)
                print("RX=" + str(RX))

                # -----  remocon 16 Code  Exit ------
                if RX == 16:
                    receiving_exit = 0
                    break

# Tx를 보낸 후 응답을 받을 때 까지 Lock을 걸기 반대쪽에서 보낸 Rx가 유실 될 수도 있으니, 일정시간이 지나도 답이 안오면 재요청

if __name__ == '__main__':
    pass