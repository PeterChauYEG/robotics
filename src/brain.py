import asyncio
import websockets
import sys
import numpy as np
from queue import Queue
from threading import Thread, Event
import time

# drone
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8000

# video stream
WIDTH = 128
HEIGHT = 112
CHANNELS = 3

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
    def __init__(self):
        pass

    def task(self, video_stream, queue_in):
        while not event.is_set():
            if video_stream[0][0][0] != 0:
                queue_in.put('forward')
                video_stream.fill(0)


class Brain:
    def __init__(self, cmd_queue, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.connected = set()
        self.cmd_queue = cmd_queue

    def start_server(self):
        print('Starting server - host: {}, port: {}'.format(self.host, self.port))
        server = websockets.serve(self.handler, self.host, self.port)
        return server

    async def handler(self, websocket):
        print('new connection')

        self.connected.add(websocket)

        try:
            await asyncio.gather(
                self.consumer_handler(websocket),
                self.producer_handler(websocket),
            )

        except Exception as e:
            print(e)
        finally:
            self.connected.remove(websocket)

        print('connection closed')

    async def consumer_handler(self, websocket):
        print('start consumer handler')

        async for msg in websocket:
            self.handle_msg(msg)
            await websocket.send('ack')


    async def producer_handler(self, websocket):
        print('start producer handler')

        while True:
            if not cmd_queue.empty():
                cmd = cmd_queue.get()
                await websocket.send(cmd)
                print('sent cmd: {}\n'.format(cmd))
            else:
                await asyncio.sleep(0.25)


    def handle_msg(self, data):
        if data == 'connected':
            print('connected\n')
        else:
            print('image received\n')
            video_stream[:] = np.frombuffer(data, dtype=np.uint8).reshape((HEIGHT, WIDTH, CHANNELS))


if __name__ == '__main__':
    print('initializing brain')

    host, port = get_args()

    brain = Brain(cmd_queue=cmd_queue, host=host, port=port)
    object_detection = ObjectDetection()

    object_detection_thread = Thread(target=object_detection.task, args=(video_stream, cmd_queue))

    loop = asyncio.get_event_loop()

    try:
        if object_detection_thread:
            object_detection_thread.start()

        print('starting loop')
        loop.run_until_complete(brain.start_server())
        loop.run_forever()
    except KeyboardInterrupt:
        print('keyboard interrupt')
        pass
    except Exception as e:
        print("Exception: {}".format(e))
        pass
    finally:
        event.set()

        if object_detection_thread and object_detection_thread.is_alive():
            object_detection_thread.join()

        loop.close()
