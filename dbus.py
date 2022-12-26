#!/usr/bin/python3

import subprocess
import pydbus

# https://fhackts.wordpress.com/2019/08/08/shutting-down-or-rebooting-over-dbus-programmatically-from-a-non-root-user/
# https://edv.mueggelland.de/das-linux-policykit-verstehen/
def powerOff():
    bus = pydbus.SystemBus()
    logind = bus.get('.login1')['.Manager']
    logind.PowerOff(True)

def reboot():
    bus = pydbus.SystemBus()
    logind = bus.get('.login1')['.Manager']
    logind.Reboot(True)
