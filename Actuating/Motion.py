import serial
import time
from threading import Thread

MOTION = {
    "SIGNAL": {"INIT": 29},
    "MODE": {"WALK": 0, "STABLE": 122, "MOVE": 15, "VIEW": 29, "TURN": 111},

    "VIEW": {"DOWN80": 0, "DOWN60": 2, "FRONT": 5, "DOWN45": 6, "DOWN30": 7},
    # 왼쪽, 오른쪽 각각 45도씩
    "DIR": {"CENTER": 21, "LEFT": 22, "RIGHT": 24},
    "SCOPE": {"SHORT": 0, "LONG": 5},
    "SPEED": {"FAST": 0, "SLOW": 3},

    "WALK": {
        "START": 8,
        "END": 101,
        "FRONT": 102,
        "BACK": 12
    },

    "GRAB": 33
}

class Motion:
    def __init__(self):
        self.serial_use = 1
        self.serial_port = None
        self.Read_RX = 0
        self.receiving_exit = 1
        self.threading_Time = 0.01
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
        pass

    def walk(self, speed=MOTION["SPEED"]["SLOW"], direction=MOTION["DIR"]["CENTER"]):
        if direction != MOTION["DIR"]["CENTER"]:
            self.TX_data_py2(direction)
        self.TX_data_py2(MOTION["MODE"]["WALK"] + MOTION["WALK"]["START"] + speed)
        pass

    def head(self, view=MOTION["VIEW"]["DOWN80"], direction=MOTION["DIR"]["CENTER"]):
        # print(type(view))
        self.TX_data_py2(direction)
        self.TX_data_py2(view)
        return self

    def move(self, direct=MOTION["DIR"]["LEFT"], repeat=1):
        for _ in range(repeat):
            self.TX_data_py2(MOTION["MODE"]["MOVE"] + direct)
        pass

    def turn(self, direct=MOTION["DIR"]["LEFT"], repeat=1):
        for _ in range(repeat):
            self.TX_data_py2(direct)
        pass

    def grab(self):
        self.TX_data_py2(MOTION["GRAB"])
        pass



# Tx를 보낸 후 응답을 받을 때 까지 Lock을 걸기 반대쪽에서 보낸 Rx가 유실 될 수도 있으니, 일정시간이 지나도 답이 안오면 재요청


if __name__ == '__main__':
    temp = Motion()
    temp.init()
    time.sleep(1)
    x = 3
    while x > 0:
        temp.walk()
        x -= 1
    time.sleep(1)
    temp.init()


