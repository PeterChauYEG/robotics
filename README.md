# robotics

## venv

### create
python3 -m venv venv

### activate
source venv/bin/activate

### deps
pip3 install sparkfun-qwiic
pip3 install websockets==4
pip3 install asyncio==3.4.3
pip3 install sparkfun_qwiic_micro_oled
sudo pip3 install sparkfun_qwiic

python3 -m pip install keyboard

----------------

## brain
sudo python3 src/brain.py 192.168.0.182 8000

### connect
ssh pi@192.168.0.247

## drone
python3 src/drone.py ws://192.168.0.182:8000

## test monitor
python3 src/oled.py

## gpio
sudo apt install wiringpi

## i2c
i2cdetect -y 1
