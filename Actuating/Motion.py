import serial
import time
from threading import Thread

MOTION = {
    "SIGNAL": {"INIT": 17},
    "MODE": {"WALK": 0, "TURN": 7, "MOVE": 19, "VIEW": 31},
    # 머리 상하좌우 회전
    "VIEW": {"DOWN": {"90": 0, "80": 1, "60": 2, "45": 3, "35": 4, "30": 5, "10": 6, "18": 17}},
    # 로봇 몸 전체 회전 10도/머리 좌우 회전
    "DIR": {"LEFT": {"DEFAULT": 0, "30": 7, "45": 8, "60": 9, "90": 10, "CENTER": 11},
            "RIGHT": {"DEFAULT": 1, "CENTER": 11, "30": 13, "45": 14, "60": 15, "90": 16}},
    "SCOPE": {"NORMAL": 0, "SHORT": 9},
    "SPEED": {"FAST": 0, "RUN": 1, "SLOW": 2}, 

    "WALK": {
        "START": 9,
        "END": 400,
        "BACK": 10
    },
    # 물건 집기, 놓기, 좌우 회전, 좌우 이동
    "GRAB": {"DISTANCE": 5, "ON": 30, "OFF": 27, "WALK": 41, "TURN": {"RIGHT": 6, "LEFT": 7},
             "MOVE": {"LEFT": 31, "RIGHT": 32}}
}


class Motion:
    def __init__(self):
        self.serial_use = 1
        self.serial_port = None
        self.Read_RX = 0
        self.receiving_exit = 1
        self.threading_Time = 0.01
        self.lock = False
        self.distance = 0
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
        self.lock = True
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
                self.distance = RX
                if RX == 100:
                    print("motion end")
                    self.lock = False
                print("RX=" + str(RX))
                # -----  remocon 16 Code  Exit ------
                if RX == 16:
                    self.receiving_exit = 0
                    break
                return RX

    def init(self):
        if not self.lock:
            self.TX_data_py2(MOTION["SIGNAL"]["INIT"])
            while self.getRx():
                continue
        pass

    def walk(self, grab=None, walk_signal=MOTION["WALK"]["START"], scope=MOTION["SCOPE"]["NORMAL"], speed=MOTION["SPEED"]["SLOW"]):
        if not self.lock:
            if grab is None:
                self.TX_data_py2(MOTION["MODE"]["WALK"] + walk_signal + speed + scope)
            elif grab is "GRAB":
                self.TX_data_py2(MOTION["MODE"]["WALK"] + MOTION["GRAB"]["WALK"] + speed + scope)
            while self.getRx():  # Until true wait
                continue
        pass

    def head(self, view=MOTION["VIEW"]["DOWN"]["90"], direction=MOTION["DIR"]["LEFT"]["CENTER"]):
        if not self.lock:
            self.TX_data_py2(MOTION["MODE"]["VIEW"] + view)
            while self.getRx():
                continue

        if not self.lock:
            self.TX_data_py2(MOTION["MODE"]["VIEW"] + direction)
            while self.getRx():
                continue
        pass

    '''def move(self, grab=None, grab_direction=MOTION["GRAB"]["MOVE"]["LEFT"], scope=MOTION["SCOPE"]["NORMAL"],
             direction=MOTION["DIR"]["LEFT"]["DEFAULT"], repeat=1):
        if not self.lock:
            if grab is None:
                for _ in range(repeat):
                    self.TX_data_py2(MOTION["MODE"]["MOVE"] + direction + scope)
            elif grab is "GRAB":
                for _ in range(repeat):
                    self.TX_data_py2(MOTION["MODE"]["MOVE"] + grab_direction + scope)
            while self.getRx():
                continue
        pass'''

    def move(self, grab=None, direction=None, scope=MOTION["SCOPE"]["NORMAL"], repeat=1):
        if not self.lock:
            if grab is None:
                if direction is "LEFT":
                    for _ in range(repeat):
                        self.TX_data_py2(MOTION["MODE"]["MOVE"] + scope + MOTION["DIR"]["LEFT"]["DEFAULT"])
                elif direction is "RIGHT":
                    for _ in range(repeat):
                        self.TX_data_py2(MOTION["MODE"]["MOVE"] + scope + MOTION["DIR"]["RIGHT"]["DEFAULT"])
            elif grab is "GRAB":
                if direction is "LEFT":
                    for _ in range(repeat):
                        self.TX_data_py2(MOTION["MODE"]["MOVE"] + scope + MOTION["GRAB"]["MOVE"]["LEFT"])
                elif direction is "RIGHT":
                    for _ in range(repeat):
                        self.TX_data_py2(MOTION["MODE"]["MOVE"] + scope + MOTION["GRAB"]["MOVE"]["RIGHT"])
            while self.getRx():
                continue
        pass


    '''def turn(self, grab=None, grab_direction=MOTION["GRAB"]["TURN"]["LEFT"],
             direction=MOTION["DIR"]["LEFT"]["DEFAULT"], repeat=1):
        if not self.lock:
            if grab is None:
                for _ in range(repeat):
                    self.TX_data_py2(direction + MOTION["MODE"]["TURN"])
            elif grab is "GRAB":
                for _ in range(repeat):
                    self.TX_data_py2(grab_direction + MOTION["MODE"]["TURN"])
            while self.getRx():
                continue
        pass'''
    
    def turn(self, grab=None, direction=None, repeat=1):
        if not self.lock:
            if grab is None:
                if direction is "LEFT":
                    for _ in range(repeat):
                        self.TX_data_py2(MOTION["DIR"]["LEFT"]["DEFAULT"] + MOTION["MODE"]["TURN"])
                elif direction is "RIGHT":
                    for _ in range(repeat):
                        self.TX_data_py2(MOTION["DIR"]["RIGHT"]["DEFAULT"] + MOTION["MODE"]["TURN"])
            elif grab is "GRAB":
                if direction is "LEFT":
                    for _ in range(repeat):
                        self.TX_data_py2(MOTION["MODE"]["TURN"] + MOTION["GRAB"]["TURN"]["LEFT"])
                elif direction is "RIGHT":
                    for _ in range(repeat):
                        self.TX_data_py2(MOTION["MODE"]["TURN"] + MOTION["GRAB"]["TURN"]["RIGHT"])
            while self.getRx():
                continue
        pass

    def grab(self, switch="ON"):
        if not self.lock:
            self.TX_data_py2(MOTION["GRAB"][switch])
            while self.getRx():
                continue
        pass

    def check_GRAB(self):
        if not self.lock:
            self.TX_data_py2(MOTION["GRAB"]["DISTANCE"])
            while self.getRx():
                continue
        return self.distance


if __name__ == '__main__':
    temp = Motion()
    x = temp.check_GRAB()
    print("거리: ", x)
    print("거리+10: ", x + 10)
    pass
