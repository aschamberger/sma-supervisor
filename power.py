#!/usr/bin/python3

# https://fhackts.wordpress.com/2019/08/08/shutting-down-or-rebooting-over-dbus-programmatically-from-a-non-root-user/
# https://edv.mueggelland.de/das-linux-policykit-verstehen/
#$ dbus-send --system --print-reply --dest=org.freedesktop.login1 /org/freedesktop/login1 "org.freedesktop.login1.Manager.PowerOff" boolean:true
#$ dbus-send --system --print-reply --dest=org.freedesktop.login1 /org/freedesktop/login1 "org.freedesktop.login1.Manager.Reboot" boolean:true

from dbus_fast import BusType, Message, MessageType, Variant
from dbus_fast.aio import MessageBus

import asyncio
import fcntl
import json
import os

# Equivalent of the _IO('U', 20) constant in the linux kernel.
USBDEVFS_RESET = ord('U') << (4*2) | 20

async def power_off():
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    reply = await bus.call(
        Message(destination='org.freedesktop.login1',
                path='/org/freedesktop/login1',
                interface='org.freedesktop.login1.Manager',
                member='PowerOff',
                signature='b',
                body=[True]))

async def reboot():
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    reply = await bus.call(
        Message(destination='org.freedesktop.login1',
                path='/org/freedesktop/login1',
                interface='org.freedesktop.login1.Manager',
                member='Reboot',
                signature='b',
                body=[True]))

async def get_usb_device_paths(id):
    devices = []
    program = [ 'lsusb' ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        lines = stdout.decode().split('\n')
        for line in lines:
            if id in line:
                parts = line.split()
                bus = parts[1]
                dev = parts[3][:3]
                devices.append(f"/dev/bus/usb/{bus}/{dev}")
    else:
        print("error")
    return devices

# Sends the USBDEVFS_RESET IOCTL to a USB device.
# https://gist.github.com/PaulFurtado/fce98aef890469f34d51
def reset_usb_device(dev_path):
    fd = os.open(dev_path, os.O_WRONLY)
    try:
        fcntl.ioctl(fd, USBDEVFS_RESET, 0)
    finally:
        os.close(fd)

async def main():
    print('reboot test')

    usb_id_dacs = "0d8c:0102"
    usb_id_hub = "1a40:0201"

    devices = await get_usb_device_paths(usb_id_dacs)
    print(devices)

    devices = await get_usb_device_paths(usb_id_hub)
    print(devices)

    #await reboot()

if __name__ == '__main__':
    asyncio.run(main())