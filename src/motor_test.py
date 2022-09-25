import qwiic
import time
import sys

R_MTR = 0
L_MTR = 1
FWD = 0
BWD = 1
speed = 20

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
    myMotor.set_drive(R_MTR, FWD, 0)
    myMotor.set_drive(L_MTR, FWD, 0)

    myMotor.enable()
    print("Motor enabled")
    time.sleep(.250)

    while True:
        myMotor.set_drive(R_MTR, FWD, speed)
        myMotor.set_drive(L_MTR, FWD, speed)
        time.sleep(2)
        myMotor.set_drive(R_MTR, FWD, 0)
        myMotor.set_drive(L_MTR, FWD, 0)

        myMotor.set_drive(R_MTR, BWD, speed)
        myMotor.set_drive(L_MTR, BWD, speed)
        time.sleep(2)
        myMotor.set_drive(R_MTR, FWD, 0)
        myMotor.set_drive(L_MTR, FWD, 0)

if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit) as exErr:
        print("Ending example.")
        myMotor.disable()
        sys.exit(0)
