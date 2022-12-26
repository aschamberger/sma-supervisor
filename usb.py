#!/usr/bin/python3

import subprocess

# https://github.com/mvp/uhubctl#raspberry-pi-3b
# uhubctl -l 1-1 -p 2 -a 0
# https://github.com/mvp/uhubctl#linux-usb-permissions
# libusb without udev support required to run within container, this is the case for alpine
def powerCycleUsb():
    p = subprocess.run( [ 'uhubctl', '-l', '1-1', '-p', '2', '-a', 'cycle', '-d', '10' ], capture_output=True, text=True )
    if p.returncode == 0: 
        print(p.stdout)
    else:
        print("error")
