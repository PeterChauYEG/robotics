# TODO: show some sweet messages for staging of startup and shutdown
# do a nicer shutdown
# do a nicer init

import asyncio
import websockets
import sys
import qwiic
from threading import Thread, Event
from queue import Queue
import time
import subprocess
from picamera import PiCamera
from io import BytesIO
import numpy as np
import picamera.array

# drone
DEFAULT_HOST = 'ws://localhost:8000'

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

# Shared memory for threads to communicate
event = Event()
monitor_queue = Queue()
drivetrain_queue = Queue()
video_stream_io = np.empty((128, 112, 3), dtype=np.uint8)


def get_args():
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return DEFAULT_HOST


def get_ip_address():
    ip = subprocess.check_output(['hostname', '-I'])
    return ip.decode('utf-8').split(' ')[0]


class VideoStream:
    def __init__(self, camera):
        self.camera = camera

    def task(self, video_stream_io):
        while not event.is_set():
            if not self.camera or self.camera.closed:
                raise Exception("Camera closed")

            self.camera.capture(video_stream_io, 'rgb')
            time.sleep(1)


class Monitor:
    def __init__(self):
        self.display = None
        self.ip = None

    def init(self):
        print("monitor starting")
        self.display = qwiic.QwiicMicroOled()

        self.display.begin()
        self.display.scroll_stop()
        self.display.clear(self.display.ALL)
        self.ip = get_ip_address()
        print("monitor complete")

    def clear(self):
        self.display.clear(self.display.PAGE)
        self.display.scroll_stop()
        self.display.set_cursor(0, 0)

    def display_ip(self):
        if self.ip:
            self.display.set_cursor(0, 16)
            self.display.print(self.ip)
        else:
            self.display.print("No Internet!")

    def display_name(self):
        self.display.set_cursor(0, 40)
        self.display.print("n i p s")

    def display_cmd(self, cmd):
        self.clear()
        self.display.print(cmd)

    def task(self, queue_in):
        self.init()

        while not event.is_set():
            if not queue_in.empty() and self.display:
                msg = queue_in.get()
                self.display_cmd(msg)
                self.display_ip()
                self.display_name()
                self.display.display()


class DriveTrain:
    def __init__(self):
        self.motorboard = None
        self.speed = DEFAULT_SPEED

    def init(self):
        print("drivetrain starting")
        self.motorboard = qwiic.QwiicScmd()

        if self.motorboard.connected == False:
            raise Exception("Motor board not connected")

        self.motorboard.begin()
        time.sleep(.250)

        self.stop()

        self.motorboard.enable()
        time.sleep(.250)

        print("drivetrain complete")

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
        if self.motorboard:
            self.stop()
            self.motorboard.disable()

    def cmd_handler(self, cmd):
        if cmd == 'forward':
            self.forward()
        elif cmd == 'backward':
            self.backward()
        elif cmd == 'left':
            self.left()
        elif cmd == 'right':
            self.right()
        elif cmd == 'stop':
            self.stop()
        else:
            print('unknown command')

    def task(self, queue_in):
        self.init()

        while not event.is_set():
            if not queue_in.empty() and self.motorboard:
                cmd = queue_in.get()
                self.cmd_handler(cmd)

        self.shutdown()


class Drone:
    def __init__(self, _host):
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
            item = np.ones((128, 112, 3), dtype=np.uint8)

            while True:
                if item[0][0][0] == 1:
                    await self.websocket.send(item.tobytes())
                    item.fill(0)

                # if video_stream_io[0][0][0] != 0:
                #     await self.websocket.send(video_stream_io.tobytes())
                #     video_stream_io.fill(0)

                # msg = await self.websocket.recv()
                # Drone.msg_handler(msg)

    @staticmethod
    def msg_handler(msg):
        print(msg)
        monitor_queue.put(msg)

        if msg == 'forward' \
                or msg == 'backward' \
                or msg == 'left' \
                or msg == 'right' \
                or msg == 'stop':
            drivetrain_queue.put(msg)
        else:
            print('unknown command')

    async def close_connection(self):
        print('closing connection')
        if self.websocket is not None:
            await self.websocket.close()
            self.websocket = None


if __name__ == '__main__':
    print('initializing drone')

    host = get_args()

    camera = PiCamera()
    camera.resolution = (128, 112)
    time.sleep(2)

    # drivetrain = DriveTrain()
    # monitor = Monitor()
    video_stream = VideoStream(camera)
    drone = Drone(host)

    drivetrain_thread = None
    monitor_thread = None
    # drivetrain_thread = Thread(target=drivetrain.task, args=(drivetrain_queue,))
    # monitor_thread = Thread(target=monitor.task, args=(monitor_queue,))
    video_stream_thread = Thread(target=video_stream.task, args=(video_stream_io,))

    loop = asyncio.get_event_loop()

    try:
        if monitor_thread:
            monitor_thread.start()

        if drivetrain_thread:
            drivetrain_thread.start()

        if video_stream_thread:
            video_stream_thread.start()

        loop.run_until_complete(drone.run())
        loop.run_forever()

    except KeyboardInterrupt:
        print('keyboard interrupt')

    except Exception as e:
        print('An error occurred {}'.format(e))

    finally:
        event.set()

        if monitor_thread and monitor_thread.is_alive():
            monitor_thread.join()

        if drivetrain_thread and drivetrain_thread.is_alive():
            drivetrain_thread.join()

        if video_stream_thread and video_stream_thread.is_alive():
            video_stream_thread.join()

        if drone is not None:
            loop.run_until_complete(drone.close_connection())

        loop.close()
