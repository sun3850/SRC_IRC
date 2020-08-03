import serial
import time
from threading import Thread

MOTION = {
    "SIGNAL": {"INIT": 32},
    "MODE": {"WALK": 0, "STABLE": 122, "MOVE": 19, "VIEW": 32, "TURN": 7},
    # 머리 상하좌우 회전
    "VIEW": {"DOWN80": 0, "DOWN60": 1, "DOWN45": 2, "DOWN35": 3, "DOWN30": 4, "DOWN10": 5},
    # 로봇 몸 전체 회전 10도/머리 좌우 회전
    "DIR": {"LEFT": 0, "RIGHT": 1, "LEFT30": 6, "LEFT45": 7, "LEFT60": 8, "LEFT90": 9, "RIGHT30": 10,
            "RIGHT45": 11, "RIGHT60": 12, "RIGHT90": 13, "CENTER": 21},
    "SCOPE": {"SHORT": 0, "LONG": 5},
    "SPEED": {"FAST": 0, "RUN": 1, "SLOW": 2},

    "WALK": {
        "START": 9,
        "END": 400,
        "FRONT": 102,
        "BACK": 28
    },

    "GRAB": 31
}

class Motion:
    def __init__(self):
        self.serial_use = 1
        self.serial_port = None
        self.Read_RX = 0
        self.receiving_exit = 1
        self.threading_Time = 0.01
        self.lock = None
        #self.distance = 99
        BPS = 4800  # 4800,9600,14400, 19200,28800, 57600, 115200

        # ---------local Serial Port : ttyS0 --------
        # ---------USB Serial Port : ttyAMA0 --------

        self.serial_port = serial.Serial('/dev/ttyS0', BPS, timeout=0.01)
        self.serial_port.flush()  # serial cls
        self.serial_t = Thread(target=self.Receiving, args=(self.serial_port,))
        self.serial_t.daemon = True
        self.serial_t.start()
        time.sleep(0.1)

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

    def getRx(self):
        return self.lock

    def Receiving(self, ser):
        #
        # global X_255_point
        # global Y_255_point
        # global X_Size
        # global Y_Size
        # global Area, Angle

        self.receiving_exit = 1
        while True:
            if self.receiving_exit == 0:
                break
            time.sleep(self.threading_Time)
            # 수신받은 데이터의 수가 0보다 크면 데이터를 읽고 출력
            while ser.inWaiting() > 0:
                # Rx, 수신
                self.lock = True
                result = ser.read(1)
                RX = ord(result)
                print("RX=" + str(RX))

                # -----  remocon 16 Code  Exit ------
                if RX == 16:
                    self.receiving_exit = 0
                    break

    '''def start(self):
        self.TX_data_py2(MOTION["SIGNAL"]["START"])
        pass'''

    def init(self):
        self.TX_data_py2(MOTION["SIGNAL"]["INIT"])
        while not self.getRx():
            print(self.getRx())
        pass

    def walk(self, walk_signal=MOTION["WALK"]["START"], speed=MOTION["SPEED"]["SLOW"]):
        if walk_signal == MOTION["WALK"]["END"]:
            self.TX_data_py2(MOTION["MODE"]["WALK"] + walk_signal)
        self.TX_data_py2(MOTION["MODE"]["WALK"] + walk_signal + speed)
        while not self.getRx():
            print(self.getRx())
        pass

    def head(self, view=MOTION["VIEW"]["DOWN80"], direction=MOTION["DIR"]["CENTER"]):
        # print(type(view))
        self.TX_data_py2(direction)
        while not self.getRx():
            print(self.getRx())
        pass

        self.TX_data_py2(view)
        while not self.getRx():
            print(self.getRx())
        pass

    def move(self, direct=MOTION["DIR"]["LEFT"], repeat=1):
        for _ in range(repeat):
            self.TX_data_py2(MOTION["MODE"]["MOVE"] + direct)
        while not self.getRx():
            print(self.getRx())
        pass

    def turn(self, direct=MOTION["DIR"]["LEFT"], repeat=1):
        for _ in range(repeat):
            self.TX_data_py2(direct + MOTION["MODE"]["TURN"])
        while not self.getRx():
            print(self.getRx())
        pass

    def grab(self):
        self.TX_data_py2(MOTION["GRAB"])
        while not self.getRx():
            print(self.getRx())
        pass

# Tx를 보낸 후 응답을 받을 때 까지 Lock을 걸기 반대쪽에서 보낸 Rx가 유실 될 수도 있으니, 일정시간이 지나도 답이 안오면 재요청


if __name__ == '__main__':
    pass


