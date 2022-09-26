import time
import picamera
import picamera.array
import numpy as np


class VideoStream:
    def __init__(self):
        self.camera = None

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

        if self.camera.closed:
            raise Exception("Camera not closed")

        image = np.empty((128, 112, 3), dtype=np.uint8)
        self.camera.capture(image, 'rgb')
        image = image[:100, :100]
        print(image[0][0])


if __name__ == '__main__':
    print('initializing camera stream test')

    stream = VideoStream()
    stream.task()
