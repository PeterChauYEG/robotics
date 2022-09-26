from picamera import PiCamera
from io import BytesIO


class VideoStream:
    def __init__(self):
        self.stream = BytesIO()
        self.camera = None

    def task(self):
        self.camera = PiCamera()

        self.camera.resolution = (100, 100)
        print("init camera complete")

        if not self.camera or self.camera.closed:
            raise Exception("Camera closed")

        try:
            self.camera.start_recording(self.stream, 'rgb')
            self.camera.wait_recording(1)
            self.camera.stop_recording()
        except Exception as e:
            print(e)
        finally:
            if self.camera:
                self.camera.close()


if __name__ == '__main__':
    print('initializing camera stream test')

    stream = VideoStream()
    stream.task()
