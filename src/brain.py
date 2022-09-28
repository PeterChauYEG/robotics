import asyncio
import websockets
import sys
from queue import Queue
from threading import Thread, Event
from transformers import pipeline
import numpy as np
from PIL import Image, ImageDraw
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

            object_center_y, object_center_x = ObjectDetection.get_offset_from_center(object)
            print('Object center: ' + str(object_center_y) + ', ' + str(object_center_x))

            if abs(object_center_y) > abs(object_center_x):
                if object_center_y < OFFSET_HEIGHT_THRESHOLD_AMOUNT:
                    print('Object is below center')
                    return 'backward'
                elif object_center_y > OFFSET_HEIGHT_THRESHOLD_AMOUNT:
                    print('Object is above center')
                    return 'forward'
                else:
                    print('Object in threshold')
                    return 'stop'
            else:
                if object_center_x < OFFSET_WIDTH_THRESHOLD_AMOUNT:
                    print('Object is to the left of center')
                    return 'left'
                elif object_center_x > OFFSET_WIDTH_THRESHOLD_AMOUNT:
                    print('Object is to the right of center')
                    return 'right'
                else:
                    print('Object in threshold')
                    return 'stop'

        else:
            print('No object found')
            return 'stop'

    @staticmethod
    def get_offset_from_center(object):
        box = object['box']
        object_center = (box['ymax'] - box['ymin']) / 2 + box['ymin'], (box['xmax'] - box['xmin']) / 2 + box['xmin']

        # 64 - ((0 - 40) / 2) = 52
        return IMG_CENTER[0] - object_center[0], IMG_CENTER[1] - object_center[1]

    @staticmethod
    def find_object(predictions):
        for prediction in predictions:
            if prediction['label'] == OBJECT and prediction['score'] > CONFIDENCE_THRESHOLD:
                return prediction
        return None

    @staticmethod
    def save_image(img_pil, predictions):
        dir_path = os.getcwd()

        # time based file name in relative path imgs yyyymmdd_hhmmss and prediction box
        path = dir_path + '/imgs/' + datetime.now().strftime("%Y%m%d_%H%M%S")

        # if prediction, add path
        object = ObjectDetection.find_object(predictions)

        if object is not None:
            object_center_y, object_center_x = ObjectDetection.get_offset_from_center(object)
            print('object_center_y: ' + str(object_center_y) + ' object_center_x: ' + str(object_center_x))
            path = path + '_y' + str(object_center_y) + '_x' + str(object_center_x)

            # add rectangle to pil image
            box = object['box']
            # get box size
            box_size = (box['xmax'] - box['xmin'], box['ymax'] - box['ymin'])
            box_shape = (box['xmin'], box['ymin']), box_size[0], box_size[1]
            draw = ImageDraw.Draw(img_pil)
            draw.rectangle(box_shape, outline='red', width=5)

            cmd = ObjectDetection.determine_command(predictions)
            path = path + '_' + cmd

        img_pil.save(path + '.jpg')

    def predict(self, img_pil):
        return self.classifier(img_pil)

    def task(self, video_stream, queue_in):
        while not event.is_set():
            if video_stream[0][0][0] != 0:
                img_pil = Image.fromarray(video_stream)

                predictions = self.predict(img_pil)

                ObjectDetection.save_image(img_pil, predictions)

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
                # await websocket.send('ack')
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
