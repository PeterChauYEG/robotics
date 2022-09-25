import qwiic
import time
import sys
import math

results = qwiic.list_devices()

print("Found %d devices" % len(results))

myMotor = qwiic.QwiicScmd()


def runExample():
    print("Motor Test.")
    R_MTR = 0
    L_MTR = 1
    FWD = 0
    BWD = 1
    speed = 20

    if myMotor.connected == False:
        print("Motor Driver not connected. Check connections.", \
              file=sys.stderr)
        return
    myMotor.begin()
    print("Motor initialized.")
    time.sleep(.250)

    # Zero Motor Speeds
    myMotor.set_drive(0, 0, 0)
    myMotor.set_drive(1, 0, 0)

    myMotor.enable()
    print("Motor enabled")
    time.sleep(.250)

    while True:
        for speed in range(20,255):
            print(speed)
            myMotor.set_drive(R_MTR,FWD,speed)
            myMotor.set_drive(L_MTR,BWD,speed)
            time.sleep(.05)
        for speed in range(254,20, -1):
            print(speed)
            myMotor.set_drive(R_MTR,FWD,speed)
            myMotor.set_drive(L_MTR,BWD,speed)
            time.sleep(.05)


if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit) as exErr:
        print("Ending example.")
        myMotor.disable()
        sys.exit(0)
