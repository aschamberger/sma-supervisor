#!/usr/bin/python3

import subprocess
import pydbus

# https://fhackts.wordpress.com/2019/08/08/shutting-down-or-rebooting-over-dbus-programmatically-from-a-non-root-user/
# https://edv.mueggelland.de/das-linux-policykit-verstehen/
# TODO add polkit rule 
def powerOff():
    bus = pydbus.SystemBus()
    logind = bus.get('.login1')['.Manager']
    logind.PowerOff(True)

def reboot():
    bus = pydbus.SystemBus()
    logind = bus.get('.login1')['.Manager']
    logind.Reboot(True)

def powerCycleUsb():
    # https://github.com/mvp/uhubctl#raspberry-pi-3b
    # uhubctl -l 1-1 -p 2 -a 0
    # TODO https://github.com/mvp/uhubctl#linux-usb-permissions
    # libusb without udev support required to run within container, this is the case for alpine
    p = subprocess.run( [ 'uhubctl', '-l', '1-1', '-p', '2', '-a', 'cycle', '-d', '10' ], capture_output=True, text=True )
    if p.returncode == 0: 
        print(p.stdout)
    else:
        print("error")
