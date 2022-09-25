# robotics

## venv

### create
python3 -m venv venv

### activate
source venv/bin/activate

### deps
pip3 install sparkfun-qwiic
pip3 install websockets
pip3 install asyncio
python3 -m pip install keyboard

----------------

## brain
sudo python3 src/ws/brain.py 192.168.0.182 8000

### connect
ssh pi@192.168.0.247

## drone
python3 src/ws/drone.py ws://192.168.0.182:8000

