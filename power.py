#!/usr/bin/python3

# https://fhackts.wordpress.com/2019/08/08/shutting-down-or-rebooting-over-dbus-programmatically-from-a-non-root-user/
# https://edv.mueggelland.de/das-linux-policykit-verstehen/
#$ dbus-send --system --print-reply --dest=org.freedesktop.login1 /org/freedesktop/login1 "org.freedesktop.login1.Manager.PowerOff" boolean:true
#$ dbus-send --system --print-reply --dest=org.freedesktop.login1 /org/freedesktop/login1 "org.freedesktop.login1.Manager.Reboot" boolean:true

from dbus_fast import BusType, Message, MessageType, Variant
from dbus_fast.aio import MessageBus

import asyncio
import json
from usb.core import find as finddev

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

def get_usb_devices(usb_id):
    devices = finddev(find_all=True,idVendor=usb_id[0], idProduct=usb_id[1])
    return devices

# https://gist.github.com/PaulFurtado/fce98aef890469f34d51
def reset_usb_device(usb_id):
    dev = finddev(idVendor=usb_id[0], idProduct=usb_id[1])
    dev.reset()

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