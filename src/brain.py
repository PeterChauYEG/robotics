import asyncio
import json
from datetime import datetime, timedelta
import websockets
import sys
from queue import Queue
from threading import Thread, Event
from transformers import pipeline
import numpy as np
from PIL import Image
import os
import random

# nav
MODES = {
    'ROAM': 'roam',
    'APPROACH': 'approach',
}
CMDS = ['stop', 'forward', 'backward', 'left', 'right', 'up', 'down']
MIN_RANDOM_CMD_DURATION = 0.25
MAX_RANDOM_CMD_DURATION = 1.25

# drone
DEFAULT_TAKE_IMAGES = False
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8000
PRODUCER_DELAY = 0.1

# video stream
WIDTH = 128
HEIGHT = 112
CHANNELS = 3

# ai
PIPELINE_TYPE = "image-classification"
MODEL_NAME = "microsoft/resnet-50"
OBJECT = 'cat'

IMG_CENTER = (HEIGHT / 2, WIDTH / 2)

CONFIDENCE_THRESHOLD = 0.25
CENTER_OFFSET_THRESHOLD = 0.1
OFFSET_HEIGHT_THRESHOLD_AMOUNT = IMG_CENTER[0] * CENTER_OFFSET_THRESHOLD
OFFSET_WIDTH_THRESHOLD_AMOUNT = IMG_CENTER[1] * CENTER_OFFSET_THRESHOLD / 2

# named args would be better
def get_args():
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    take_images = DEFAULT_TAKE_IMAGES

    if len(sys.argv) >= 3:
        host = sys.argv[1]
        port = sys.argv[2]
        take_images = sys.argv[3] == 'true'

    return host, port, take_images


# determine how to move
# when an object is detected, move forward
# otherwise, roam mode
# move left then move forward
# utilizes a global state to determine if something has been detected
# utilizes a global state to determine if the drone just moved left
# perhaps a cmd queue would be better
# and it gets cleared when the drone detects something
class Nav:
    def __init__(self):
        self.mode = MODES['ROAM']
        self.last_cmd_started = datetime.now()
        self.last_cmd_duration = 0

    def check_cmd_duration(self):
        return self.last_cmd_started + timedelta(seconds=self.last_cmd_duration) >= datetime.now()

    @staticmethod
    def get_random_cmd():
        return random.choice(CMDS)

    @staticmethod
    def get_random_duration():
        return random.uniform(MIN_RANDOM_CMD_DURATION, MAX_RANDOM_CMD_DURATION)

    def task(self, cmd_queue, detected):
        while not event.is_set():
            cmd = {
                'action': 'stop',
                'speed': 0
            }

            if detected:
                if self.check_cmd_duration() or self.mode == MODES['ROAM']:
                    cmd_queue.queue.clear()

                    self.last_cmd_started = datetime.now()
                    self.mode = MODES['APPROACH']
                    self.last_cmd_duration = 0.5

                    cmd['action'] = 'forward'
                    cmd['speed'] = 50
                    
                    string_cmd = json.dumps(cmd)
                    cmd_queue.put(string_cmd)

            else:
                if self.check_cmd_duration():
                    self.last_cmd_started = datetime.now()
                    self.mode = MODES['ROAM']
                    self.last_cmd_duration = Nav.get_random_duration()

                    cmd['action'] = Nav.get_random_cmd()
                    cmd['speed'] = 60

                    string_cmd = json.dumps(cmd)
                    cmd_queue.put(string_cmd)


class ObjectDetection:
    def __init__(self, _classifier, _take_images):
        self.classifier = _classifier
        self.take_images = _take_images

    @staticmethod
    def determine_command(object_center_y, object_center_x):
        pass

    @staticmethod
    def find_object(predictions):
        for prediction in predictions:
            if prediction['score'] > CONFIDENCE_THRESHOLD:
                if OBJECT in prediction['label']:
                    return prediction
        return None

    @staticmethod
    def save_image(img_pil, cmd, label):
        dir_path = os.getcwd()
        cap_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = dir_path + '/imgs/' + cap_time + '_' + label + '_' + cmd + '.jpg'

        img_pil.save(path)

    def predict(self, img_pil):
        return self.classifier(img_pil)

    def task(self, video_stream, detected):
        while not event.is_set():
            if video_stream[0][0][0] != 0:
                img_pil = Image.fromarray(video_stream)
                predictions = self.predict(img_pil)
                detected_object = ObjectDetection.find_object(predictions)

                if detected_object is not None:
                    label = detected_object['label']
                    score = round(detected_object['score'] * 100, 2)
                    cmd = 'forward'

                    detected.set()

                    print('Detected object: ', label, ' with confidence: ', score, '%')

                    if self.take_images:
                        ObjectDetection.save_image(img_pil, cmd, label)

                else:
                    detected.clear()
                    print('No object detected')

                video_stream.fill(0)


class WsServer:
    @staticmethod
    async def handler(websocket):
        print('new connection')

        try:
            await asyncio.gather(
                WsServer.consumer_handler(websocket),
                WsServer.producer_handler(websocket),
            )

        except Exception as e:
            print(e)

        print('connection closed')

    @staticmethod
    async def consumer_handler(websocket):
        async for msg in websocket:
            WsServer.handle_msg(msg)

    @staticmethod
    async def producer_handler(websocket):
        while not event.is_set():
            if not cmd_queue.empty():
                cmd = cmd_queue.get()
                await websocket.send(cmd)
                print('sent cmd: {}\n'.format(cmd))
            else:
                await asyncio.sleep(PRODUCER_DELAY)

    @staticmethod
    def handle_msg(data):
        if data == 'connected':
            print('connected\n')
        else:
            print('image received')
            video_stream[:] = np.frombuffer(data, dtype=np.uint8).reshape((HEIGHT, WIDTH, CHANNELS))


if __name__ == '__main__':
    print('initializing brain')

    # args
    host, port, take_images = get_args()

    # Shared memory for threads to communicate
    event = Event()
    video_stream = np.zeros((HEIGHT, WIDTH, CHANNELS), dtype=np.uint8)
    cmd_queue = Queue()
    detected = Event()

    # init
    classifier = pipeline(PIPELINE_TYPE, model=MODEL_NAME)

    object_detection = ObjectDetection(classifier, take_images)
    nav = Nav()

    # threads
    object_detection_thread = Thread(target=object_detection.task, args=(video_stream, detected))
    nav_thread = Thread(target=nav.task, args=(cmd_queue, detected))

    loop = asyncio.get_event_loop()

    try:
        # start threads
        if object_detection_thread:
            object_detection_thread.start()

        if nav_thread:
            nav_thread.start()

        server = websockets.serve(WsServer.handler, host, port)
        print('starting server - host: {}, port: {}'.format(host, port))

        loop.run_until_complete(server)
        loop.run_forever()

    except KeyboardInterrupt:
        print('keyboard interrupt')
        pass

    except Exception as e:
        print("Exception: {}".format(e))
        pass

    finally:
        print('shutting down')
        event.set()

        if object_detection_thread and object_detection_thread.is_alive():
            object_detection_thread.join()

        if nav_thread and nav_thread.is_alive():
            nav_thread.join()

        loop.close()
