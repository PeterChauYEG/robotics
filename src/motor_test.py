import qwiic
import time
import sys

R_MTR = 0
L_MTR = 1
FWD = 0
BWD = 1
SPEED = 255

results = qwiic.list_devices()

print("Found %d devices" % len(results))

myMotor = qwiic.QwiicScmd()


def runExample():
    print("Motor Test.")


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

    print("Motor Test: Forward")
    myMotor.set_drive(R_MTR, FWD, SPEED)
    myMotor.set_drive(L_MTR, FWD, SPEED)
    time.sleep(1)

    print("Motor Test: Backward")
    myMotor.set_drive(R_MTR, FWD, -SPEED)
    myMotor.set_drive(L_MTR, FWD, -SPEED)
    time.sleep(1)

    print("Motor Test: Left")
    myMotor.set_drive(R_MTR, FWD, SPEED)
    myMotor.set_drive(L_MTR, FWD, -SPEED)
    time.sleep(1)

    print("Motor Test: Right")
    myMotor.set_drive(R_MTR, FWD, -SPEED)
    myMotor.set_drive(L_MTR, FWD, SPEED)
    time.sleep(1)

    print("Motor Test: Stop")
    myMotor.set_drive(R_MTR, FWD, 0)
    myMotor.set_drive(L_MTR, FWD, 0)
    myMotor.disable()

if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit) as exErr:
        print("Ending example.")
        myMotor.disable()
        sys.exit(0)
