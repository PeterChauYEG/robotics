import asyncio
import websockets
import sys
from queue import Queue
from threading import Thread, Event
from transformers import pipeline
import numpy as np
from PIL import Image
from datetime import datetime
import os

# drone
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8000
PRODUCER_DELAY = 0.1

# video stream
WIDTH = 128
HEIGHT = 112
CHANNELS = 3

# ai
PIPELINE_TYPE = "object-detection"
MODEL_NAME = "hustvl/yolos-tiny"
OBJECT = 'cat'

IMG_CENTER = (HEIGHT / 2, WIDTH / 2)

CONFIDENCE_THRESHOLD = 0.6
CENTER_OFFSET_THRESHOLD = 0.1
OFFSET_HEIGHT_THRESHOLD_AMOUNT = IMG_CENTER[0] * CENTER_OFFSET_THRESHOLD
OFFSET_WIDTH_THRESHOLD_AMOUNT = IMG_CENTER[1] * CENTER_OFFSET_THRESHOLD / 2

# Shared memory for threads to communicate
event = Event()
video_stream = np.zeros((HEIGHT, WIDTH, CHANNELS), dtype=np.uint8)
cmd_queue = Queue()


def get_args():
    host = DEFAULT_HOST
    port = DEFAULT_PORT

    if len(sys.argv) >= 1:
        host = sys.argv[1]

    if len(sys.argv) >= 2:
        port = sys.argv[2]

    return host, port


class ObjectDetection:
    def __init__(self, _classifier):
        self.classifier = _classifier

    @staticmethod
    def determine_command(predictions):
        object = ObjectDetection.find_object(predictions)

        if object is not None:
            print('Found object: ' + object['label'])

            left, top, right, bottom = ObjectDetection.find_distance_of_box_from_center(object)
            print('Left: ' + str(left) + ' Top: ' + str(top) + ' Right: ' + str(right) + ' Bottom: ' + str(bottom))

            # find largest value of left, top, right, bottom
            largest = max(left, top, right, bottom)

            if largest == left:
                if left > OFFSET_WIDTH_THRESHOLD_AMOUNT:
                    print('Object is to the left of center')
                    return 'left'
                return 'stop'
            elif largest == top:
                if top > OFFSET_HEIGHT_THRESHOLD_AMOUNT:
                    print('Object is above center')
                    return 'backward'
                return 'stop'
            elif largest == right:
                if right > OFFSET_WIDTH_THRESHOLD_AMOUNT:
                    print('Object is to the right of center')
                    return 'right'
                return 'stop'
            elif largest == bottom:
                if bottom > OFFSET_HEIGHT_THRESHOLD_AMOUNT:
                    print('Object is below center')
                    return 'forward'
                return 'stop'

        else:
            print('No object found')
            return 'stop'

    @staticmethod
    def find_distance_of_box_from_center(object):
        box = object['box']
        return box['ymin'], HEIGHT - box['ymax'], box['xmin'], WIDTH - box['xmax']

    @staticmethod
    def find_object(predictions):
        for prediction in predictions:
            if prediction['label'] == OBJECT and prediction['score'] > CONFIDENCE_THRESHOLD:
                return prediction
        return None

    @staticmethod
    def save_image(img_pil):
        dir_path = os.getcwd()

        # time based file name in relative path imgs yyyymmdd_hhmmss.jpg
        img_pil.save(dir_path + '/imgs/' + datetime.now().strftime("%Y%m%d_%H%M%S") + '.jpg')

    def predict(self, img_pil):
        return self.classifier(img_pil)

    def task(self, video_stream, queue_in):
        while not event.is_set():
            if video_stream[0][0][0] != 0:
                img_pil = Image.fromarray(video_stream)

                ObjectDetection.save_image(img_pil)

                predictions = self.predict(img_pil)
                cmd = ObjectDetection.determine_command(predictions)
                queue_in.put(cmd)
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
        while True:
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
    host, port = get_args()

    # init
    classifier = pipeline(PIPELINE_TYPE, model=MODEL_NAME)

    object_detection = ObjectDetection(classifier)

    # threads
    object_detection_thread = Thread(target=object_detection.task, args=(video_stream, cmd_queue))

    loop = asyncio.get_event_loop()

    try:
        # start threads
        print('\nstarting threads')
        if object_detection_thread:
            object_detection_thread.start()

        print('starting server - host: {}, port: {}'.format(host, port))
        server = websockets.serve(WsServer.handler, host, port)

        print('starting loop\n')
        loop.run_until_complete(server)
        loop.run_forever()

    except KeyboardInterrupt:
        print('keyboard interrupt')
        pass

    except Exception as e:
        print("Exception: {}".format(e))
        pass

    finally:
        print('closing threads')
        event.set()

        if object_detection_thread and object_detection_thread.is_alive():
            object_detection_thread.join()

        print('closing loop')
        loop.close()
