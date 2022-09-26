import time
import picamera
import picamera.array
import numpy as np
from io import BytesIO


class VideoStream:
    def __init__(self):
        self.stream = BytesIO()

    def task(self):
        with picamera.PiCamera() as camera:
            camera.resolution = (100, 100)
            print("init camera complete")

            if not camera or camera.closed:
                raise Exception("Camera closed")

            try:
                camera.start_recording(self.stream, 'rgb')
                camera.wait_recording(1)
                camera.stop_recording()

                print(self.stream.getvalue())
            except Exception as e:
                print(e)
            finally:
                camera.close()


if __name__ == '__main__':
    print('initializing camera stream test')

    stream = VideoStream()
    stream.task()
