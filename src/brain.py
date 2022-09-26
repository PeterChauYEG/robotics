import asyncio
import websockets
import keyboard
import sys
import numpy as np

video_stream = np.empty((128, 112, 3), dtype=np.uint8)


class Brain:
    def __init__(self, host='localhost', port=8000, debounce=0.5):
        self.key_pressed = False
        self.debounce = debounce
        self.host = host
        self.port = port
        self.websocket = None
        self.connected = False

    def start_server(self):
        print('Starting server... host: {}, port: {}'.format(self.host, self.port))
        server = websockets.serve(self.handler, self.host, self.port)
        return server

    async def handler(self, websocket, path):
        if self.websocket is None:
            self.websocket = websocket

        try:
            while True:
                if self.connected is False:
                    data = await websocket.recv()
                    self.handle_msg(data)
                    continue

                if self.websocket is None:
                    print('websocket is None')

                # wait for response and debounce key press
                if self.key_pressed:
                    data = await self.websocket.recv()

                    self.handle_msg(data)
                    await self.debounce_keyboard_input()

                # get and handle keyboard input
                keyboard_input = Brain.get_keyboard_input()
                await self.handle_keyboard_input(keyboard_input)

        except Exception as e:
            print("Exception: {}".format(e))
            self.connected = False
            self.websocket = None

    def handle_msg(self, data):
        if data == 'received':
            print('received\n')
            self.key_pressed = False
        elif data == 'connected':
            print('connected')
            self.connected = True
        else:
            print(data)
            video_stream[:] = np.frombuffer(data, dtype=np.uint8).reshape((128, 112, 3))
            print(video_stream)


    async def debounce_keyboard_input(self):
        await asyncio.sleep(self.debounce)

    @staticmethod
    def get_keyboard_input():
        event = keyboard.read_event()

        if event.event_type == keyboard.KEY_DOWN:
            if keyboard.is_pressed('q'):
                return 'exit'

            elif keyboard.is_pressed('w'):
                return 'forward'

            elif keyboard.is_pressed('s'):
                return 'backward'

            elif keyboard.is_pressed('a'):
                return 'left'

            elif keyboard.is_pressed('d'):
                return 'right'

            elif keyboard.is_pressed(' '):
                return 'stop'

        return None

    async def handle_keyboard_input(self, keyboard_input):
        if keyboard_input is None:
            return

        if keyboard_input == 'exit':
            raise Exception("User exited")

        else:
            self.key_pressed = True
            print(keyboard_input)
            await self.websocket.send(keyboard_input)


if __name__ == '__main__':
    print('initializing brain')
    host = 'localhost'
    port = 8000

    if len(sys.argv) >= 1:
        host = sys.argv[1]

    if len(sys.argv) >= 2:
        port = sys.argv[2]

    brain = Brain(host=host, port=port, debounce=0.1)

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

