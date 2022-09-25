import asyncio
import websockets


class Drone:
    def forward(self, speed=0.5):
        print('forward {}'.format(speed))

    def backward(self, speed=0.5):
        print('backward {}'.format(speed))

    def left(self, speed=0.5):
        print('left {}'.format(speed))

    def right(self, speed=0.5):
        print('right {}'.format(speed))

    def stop(self):
        print('stop')


class Controller:
    def __init__(self, _drone, _host):
        self.drone = _drone
        self.host = _host
        self.websocket = None

    async def run(self):
        print('connecting to {}'.format(self.host))
        return await self.connect_with_retries()

    async def connect_with_retries(self):
        async with websockets.connect(self.host) as websocket:
            try:
                print('connected')
                self.websocket = websocket
                await self.websocket.send('connected')
                await self.loop()

            except websockets.exceptions.ConnectionClosed:
                print('connection closed')
                self.websocket = None

    async def loop(self):
        if self.websocket is not None and self.websocket.open:
            while True:
                msg = await self.websocket.recv()
                await self.websocket.send("received")
                self.msg_handler(msg)

    def msg_handler(self, msg):
        print(msg)

        if msg == 'forward':
            self.drone.forward()
        elif msg == 'backward':
            self.drone.backward()
        elif msg == 'left':
            self.drone.left()
        elif msg == 'right':
            self.drone.right()
        elif msg == 'stop':
            self.drone.stop()
        else:
            print('unknown command')

    async def close_connection(self):
        print('closing connection')
        if self.websocket is not None:
            await self.websocket.close()
            self.websocket = None


if __name__ == '__main__':
    print('initializing drone')

    host = 'ws://192.168.0.182:8000'
    drone = Drone()
    controller = Controller(drone, host)

    loop = asyncio.get_event_loop()

    try:
        print('starting controller')
        loop.run_until_complete(controller.run())
        loop.run_forever()

    except KeyboardInterrupt:
        print('keyboard interrupt')

        if controller is not None:
            loop.run_until_complete(controller.close_connection())

    except Exception as e:
        print('An error occurred {}'.format(e))

    finally:
        loop.close()
