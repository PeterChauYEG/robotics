import asyncio
import websockets
import sys
import numpy as np
from queue import Queue
from threading import Thread, Event

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


class Brain:
    def __init__(self, cmd_queue, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.websocket = None
        self.connected = set()
        self.cmd_queue = cmd_queue

    def start_server(self):
        print('Starting server - host: {}, port: {}'.format(self.host, self.port))
        server = websockets.serve(self.handler, self.host, self.port)
        return server

    async def handler(self, websocket, path):
        self.websocket = websocket
        self.connected.add(self.websocket)

        try:
            consumer_task = asyncio.create_task(self.consumer_handler())
            producer_task = asyncio.create_task(self.producer_handler())

            done, pending = await asyncio.wait(
                [consumer_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()
        except Exception as e:
            print(e)
        finally:
            self.connected.remove(self.websocket)

    async def consumer_handler(self):
        async for msg in self.websocket:
            self.handle_msg(msg)

    async def producer_handler(self):
        while True:
            if not cmd_queue.empty():
                cmd = cmd_queue.get()
                await self.websocket.send(cmd)

    def handle_msg(self, data):
        if data == 'connected':
            print('connected')
            self.connected = True
        else:
            print('image received')
            video_stream[:] = np.frombuffer(data, dtype=np.uint8).reshape((HEIGHT, WIDTH, CHANNELS))


if __name__ == '__main__':
    print('initializing brain')

    host, port = get_args()

    brain = Brain(cmd_queue=cmd_queue, host=host, port=port)

    loop = asyncio.get_event_loop()

    try:
        print('starting brain')
        loop.run_until_complete(brain.start_server())
        loop.run_forever()
    except KeyboardInterrupt:
        print('keyboard interrupt')
        pass
    except Exception as e:
        print("Exception: {}".format(e))
        pass
    finally:
        loop.close()
