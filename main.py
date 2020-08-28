from Brain.Controller import Robot
if __name__ == "__main__":
    robot = Robot()
    robot.traceTarget()
    #robot.mean_tracking()
    # 두개 같이 있어야됨
    robot.checkCitizen()
    robot.walking()