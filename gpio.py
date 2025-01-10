#!/usr/bin/python3

#gdbus introspect --system --dest io.gpiod1 --object-path /io/gpiod1/chips/
#gdbus introspect --system --dest io.gpiod1 --object-path /io/gpiod1/chips/gpiochip0/line7

from dbus_fast import BusType, Message, MessageType, Variant
from dbus_fast.aio import MessageBus

import asyncio
import json

_BOARD_MAP = {
    3: 2, 
    5: 3, 
    7: 4, 
    8: 14, 
    10: 15, 
    11: 17, 
    12: 18, 
    13: 27, 
    15: 22, 
    16: 23,
    18: 24, 
    19: 10, 
    21: 9, 
    22: 25, 
    23: 11, 
    24: 8, 
    26: 7, 
    29: 5, 
    31: 6, 
    32: 12,
    33: 13, 
    35: 19, 
    36: 16, 
    37: 26, 
    38: 20, 
    40: 21,
}

# direction: input|output|as-is
async def init(board_number, direction="output", active_low=False, value=None):
    gpio = _BOARD_MAP[board_number]
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    reply = await bus.call(
        Message(destination='io.gpiod1',
                path=f'/io/gpiod1/chips/gpiochip0/line{gpio}',
                interface='org.freedesktop.DBus.Properties',
                member='Get',
                signature='ss',
                body=['io.gpiod1.Line', 'Managed']))

    if reply.message_type == MessageType.ERROR:
        raise Exception(reply.body[0])

    # if not yet initialized
    if not reply.body[0].value:
        # request line config: (a(aua{sv})ai)
        # @see: https://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.git/tree/dbus/client/common.c#n528
        line_offsets = [gpio]
        line_settings = {
            "direction": Variant('s', direction),
            "active-low": Variant('b', active_low),            
        }
        line_config = [line_offsets, line_settings]
        line_configs = [line_config]
        output_values = []
        if not value == None:
            output_values = [value]
        request_line_config = [line_configs, output_values]
        # request options: a{sv}
        request_options = {
            "consumer": Variant('s', "gpio-manager")
        }
        
        reply = await bus.call(
            Message(destination='io.gpiod1',
                    path='/io/gpiod1/chips/gpiochip0',
                    interface='io.gpiod1.Chip',
                    member='RequestLines',
                    signature='(a(aua{sv})ai)a{sv}',
                    body=[request_line_config, request_options])) #TODO

        if reply.message_type == MessageType.ERROR:
            raise Exception(reply.body[0])

        return reply.body[0]

async def get(board_number):
    gpio = _BOARD_MAP[board_number]
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    reply = await bus.call(
        Message(destination='io.gpiod1',
                path=f'/io/gpiod1/chips/gpiochip0/line{gpio}',
                interface='org.freedesktop.DBus.Properties',
                member='GetAll',
                signature='s',
                body=['io.gpiod1.Line']))

    if reply.message_type == MessageType.ERROR:
        raise Exception(reply.body[0])
   
    line_info = reply.body[0]

    reply = await bus.call(
        Message(destination='io.gpiod1',
                path=line_info['RequestPath'].value,
                interface='io.gpiod1.Request',
                member='GetValues',
                signature='au',
                body=[[line_info['Offset'].value]]))

    if reply.message_type == MessageType.ERROR:
        raise Exception(reply.body[0])
   
    return reply.body[0][0]

async def set(board_number, value):
    gpio = _BOARD_MAP[board_number]
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()

    reply = await bus.call(
        Message(destination='io.gpiod1',
                path=f'/io/gpiod1/chips/gpiochip0/line{gpio}',
                interface='org.freedesktop.DBus.Properties',
                member='GetAll',
                signature='s',
                body=['io.gpiod1.Line']))

    if reply.message_type == MessageType.ERROR:
        raise Exception(reply.body[0])
   
    line_info = reply.body[0]

    reply = await bus.call(
        Message(destination='io.gpiod1',
                path=line_info['RequestPath'].value,
                interface='io.gpiod1.Request',
                member='SetValues',
                signature='a{ui}',
                body=[{line_info['Offset'].value: value}]))

    if reply.message_type == MessageType.ERROR:
        raise Exception(reply.body[0])

async def main():
    print('gpio test')

    res = await init(26)
    print(res)
    
    res = await get(26)
    print(res)
    await set(26, 1)
    res = await get(26)
    print(res)
    await set(26, 0)
    res = await get(26)
    print(res)

if __name__ == '__main__':
    asyncio.run(main())