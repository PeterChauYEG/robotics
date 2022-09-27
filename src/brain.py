import asyncio
import websockets
import sys
from queue import Queue
from threading import Thread, Event
from transformers import pipeline
import numpy as np
from PIL import Image

# drone
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8000

# video stream
WIDTH = 128
HEIGHT = 112
CHANNELS = 3

# ai
PIPELINE_TYPE = "object-detection"
OBJECT = 'cat'

IMG_CENTER = (HEIGHT / 2, WIDTH / 2)

CONFIDENCE_THRESHOLD = 0.6
CENTER_OFFSET_THRESHOLD = 0.1
OFFSET_HEIGHT_THRESHOLD_AMOUNT = IMG_CENTER[0] * CENTER_OFFSET_THRESHOLD
OFFSET_WIDTH_THRESHOLD_AMOUNT = IMG_CENTER[1] * CENTER_OFFSET_THRESHOLD

# Shared memory for threads to communicate
event = Event()
video_stream = np.empty((HEIGHT, WIDTH, CHANNELS), dtype=np.uint8)
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
            center_offset = ObjectDetection.get_offset_from_center(object)

            if center_offset[0] > OFFSET_HEIGHT_THRESHOLD_AMOUNT:
                return 'forward'
            elif center_offset[0] < OFFSET_HEIGHT_THRESHOLD_AMOUNT:
                return 'backward'
            elif center_offset[1] > OFFSET_WIDTH_THRESHOLD_AMOUNT:
                return 'left'
            elif center_offset[1] < OFFSET_HEIGHT_THRESHOLD_AMOUNT:
                return 'right'
            else:
                return 'stop'
        else:
            return 'stop'

    @staticmethod
    def get_offset_from_center(object):
        # based on the prediction's box's xmin xmax ymin ymax determine the offset from the center
        box_center = ((object['box']['ymin'] + object['box']['ymax']) / 2, (object['box']['xmin'] + object['box']['xmax']) / 2)
        return (box_center[0] - IMG_CENTER[0], box_center[1] - IMG_CENTER[1])

    @staticmethod
    def find_object(predictions):
        for prediction in predictions:
            if prediction['label'] == OBJECT and prediction['score'] > CONFIDENCE_THRESHOLD:
                return prediction
        return None

    def predict(self, img_np):
        img = Image.fromarray(img_np)
        return self.classifier(img)

    def task(self, video_stream, queue_in):
        while not event.is_set():
            if video_stream[0][0][0] != 0:
                predictions = self.predict(video_stream)
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
            await websocket.send('ack')

    @staticmethod
    async def producer_handler(websocket):
        while True:
            if not cmd_queue.empty():
                cmd = cmd_queue.get()
                await websocket.send(cmd)
                print('sent cmd: {}\n'.format(cmd))
            else:
                await asyncio.sleep(0.25)

    @staticmethod
    def handle_msg(data):
        if data == 'connected':
            print('connected\n')
        else:
            print('image received\n')
            video_stream[:] = np.frombuffer(data, dtype=np.uint8).reshape((HEIGHT, WIDTH, CHANNELS))


if __name__ == '__main__':
    print('initializing brain')

    # args
    host, port = get_args()

    # init
    classifier = pipeline(PIPELINE_TYPE)

    object_detection = ObjectDetection(classifier)

    # threads
    object_detection_thread = Thread(target=object_detection.task, args=(video_stream, cmd_queue))

    loop = asyncio.get_event_loop()

    try:
        # start threads
        print('starting threads')
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
