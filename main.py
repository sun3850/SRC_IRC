from Brain.Controller import Robot
import argparse
import sys
parser = argparse.ArgumentParser()
parser.add_argument('-f','--filename', default='out', type=str, help='filename')
args = parser.parse_args()
if __name__ == "__main__":
    robot = Robot(record=True,filename=args.filename)
    robot.traceTarget()
    #robot.mean_tracking()
