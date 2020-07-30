from Brain.Controller import Robot

if __name__ == "__main__":
    robot = Robot()
    robot.start()
    if robot.mission == 1:
        robot.traceYellowLine()

