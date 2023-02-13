#!/usr/bin/python3

# https://fhackts.wordpress.com/2019/08/08/shutting-down-or-rebooting-over-dbus-programmatically-from-a-non-root-user/
# https://edv.mueggelland.de/das-linux-policykit-verstehen/
#$ dbus-send --system --print-reply --dest=org.freedesktop.login1 /org/freedesktop/login1 "org.freedesktop.login1.Manager.PowerOff" boolean:true
#$ dbus-send --system --print-reply --dest=org.freedesktop.login1 /org/freedesktop/login1 "org.freedesktop.login1.Manager.Reboot" boolean:true

from dbus_fast import BusType, Message, MessageType, Variant
from dbus_fast.aio import MessageBus

import asyncio
import json

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

if __name__ == '__main__':
    print('reboot test')

    asyncio.run(reboot())
