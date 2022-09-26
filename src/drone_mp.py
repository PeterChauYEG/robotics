# TODO: show some sweet messages for staging of startup and shutdown
# do a nicer shutdown
# do a nicer init

import asyncio
import websockets
import sys
import qwiic
from threading import Thread
from queue import Queue
import time

# monitor
LCDWIDTH = 64

# drivetrain
R_MTR = 0
L_MTR = 1
FWD = 0
BWD = 1
MAX_SPEED = 255
DEFAULT_SPEED = 100
STOP_SPEED = 0


monitor_queue = Queue()


class Monitor:
    def __init__(self):
        self.display = None

    def init(self):
        self.display = qwiic.QwiicMicroOled()

        self.display.begin()
        self.display.scroll_stop()
        self.display.set_font_type(0)
        self.clear()

    def clear(self):
        self.display.clear(self.display.PAGE)
        self.display.clear(self.display.ALL)
        self.display.set_cursor(0, 0)

    def display_ip(self, ip):
        self.clear()

        if ip:
            self.display.print("ip: ")
            self.display.set_cursor(0, 8)
            self.display.print(ip)
        else:
            self.display.print("No Internet!")

        self.display.display()

    def display_cmd(self, cmd):
        self.clear()

        self.display.print("cmd: ")
        self.display.set_cursor(0, 8)
        self.display.print(cmd)

        self.display.display()

    def task(self, queue_in):
        print("monitor task started")

        while True:
            if not queue_in.empty():
                msg = queue_in.get()
                self.display_cmd(msg)


class DriveTrain:
    def __init__(self):
        self.motorboard = None
        self.speed = DEFAULT_SPEED

    def init(self):
        self.motorboard = qwiic.QwiicScmd()

        if self.motorboard.connected == False:
            raise Exception("Motor board not connected")

        self.motorboard.begin()
        print("Motor initialized.")
        time.sleep(.250)

        self.stop()

        self.motorboard.enable()
        print("Motor enabled")
        time.sleep(.250)

    def stop(self):
        self.motorboard.set_drive(R_MTR, FWD, STOP_SPEED)
        self.motorboard.set_drive(L_MTR, FWD, STOP_SPEED)

    def forward(self):
        self.motorboard.set_drive(R_MTR, FWD, self.speed)
        self.motorboard.set_drive(L_MTR, FWD, self.speed)

    def backward(self):
        self.motorboard.set_drive(R_MTR, FWD, -self.speed)
        self.motorboard.set_drive(L_MTR, FWD, -self.speed)

    def left(self):
        self.motorboard.set_drive(R_MTR, FWD, self.speed)
        self.motorboard.set_drive(L_MTR, FWD, -self.speed)

    def right(self):
        self.motorboard.set_drive(R_MTR, FWD, -self.speed)
        self.motorboard.set_drive(L_MTR, FWD, self.speed)

    def set_speed(self, speed):
        self.speed = speed

    def shutdown(self):
        self.stop()
        self.motorboard.disable()


class Drone:
    def __init__(self, _drivetrain, _host):
        self.drivetrain = _drivetrain
        self.host = _host

        self.websocket = None

    async def run(self):
        print('connecting to {}'.format(self.host))
        return await self.connect_to_server()

    async def connect_to_server(self):
        async with websockets.connect(self.host) as websocket:
            try:
                print('connected')
                self.websocket = websocket
                await self.websocket.send('connected')
                await self.loop()

            except websockets.exceptions.ConnectionClosed:
                print('connection closed')
                self.websocket = None

    async def loop(self):
        if self.websocket is not None and self.websocket.open:
            while True:
                msg = await self.websocket.recv()
                await self.websocket.send("received")
                self.msg_handler(msg)

    def msg_handler(self, msg):
        print(msg)
        monitor_queue.put(msg)

        if msg == 'forward':
            self.drivetrain.forward()
        elif msg == 'backward':
            self.drivetrain.backward()
        elif msg == 'left':
            self.drivetrain.left()
        elif msg == 'right':
            self.drivetrain.right()
        elif msg == 'stop':
            self.drivetrain.stop()
        else:
            print('unknown command')

    async def close_connection(self):
        print('closing connection')
        if self.websocket is not None:
            await self.websocket.close()
            self.websocket = None

    def shutdown(self):
        if self.drivetrain is not None:
            self.drivetrain.shutdown()


if __name__ == '__main__':
    print('initializing drone')

    host = 'ws://localhost:8000'

    if len(sys.argv) >= 1:
        host = sys.argv[1]

    drivetrain = DriveTrain()
    drivetrain.init()

    monitor = Monitor()
    monitor.init()
    monitor_thread = Thread(target=monitor.task, args=(monitor_queue,))

    drone = Drone(drivetrain, host)

    loop = asyncio.get_event_loop()

    try:
        print('starting drone')
        monitor_thread.start()
        
        loop.run_until_complete(drone.run())
        loop.run_forever()

    except KeyboardInterrupt:
        print('keyboard interrupt')

    except Exception as e:
        print('An error occurred {}'.format(e))

    finally:
        if monitor_thread.is_alive():
            monitor_thread.join()

        if drone is not None:
            loop.run_until_complete(drone.close_connection())

            if drone.drivetrain is not None:
                drone.drivetrain.shutdown()

        loop.close()
