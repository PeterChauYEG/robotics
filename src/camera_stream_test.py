import time
import picamera
import picamera.array
import numpy as np
from io import BytesIO


class VideoStream:
    def __init__(self):
        self.camera = None
        self.stream = BytesIO()

    def init(self):
        print("init camera starting")

        with picamera.PiCamera() as camera:
            self.camera = camera
            self.camera.resolution = (100, 100)
            # self.camera.framerate = 24
            time.sleep(2)
            print("init camera complete")

    def task(self):
        self.init()

        if not self.camera or self.camera.closed:
            raise Exception("Camera closed")

        try:
            self.camera.start_recording(self.stream, 'rgb')
            self.camera.wait_recording(1)
            self.camera.stop_recording()

            print(self.stream.getvalue())
        except Exception as e:
            print(e)
        finally:
            self.camera.close()


if __name__ == '__main__':
    print('initializing camera stream test')

    stream = VideoStream()
    stream.task()
