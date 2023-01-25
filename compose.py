#!/usr/bin/python3

import subprocess
from dotenv.main import get_key, set_key

envFile = "/etc/opt/compose/.env"

# created, restarting, running, removing, paused, exited and dead
def containerStatus():
    p = subprocess.run( [ 'docker', 'ps', '--format', '{{.Names}}:{{.State}}' ], capture_output=True, text=True )
    if p.returncode == 0: 
        return extractContainerStatus(p.stdout)
    else:
        print("error")

def extractContainerStatus(result):
    lines = result.split("\n")
    status = {}
    for line in lines:
        if len(line) > 0: 
            line = line.split(':')
            status[line[0]] = line[1] 
    return status

def up(profile):
    p = subprocess.run( [ 'docker', 'compose', '--env-file', envFile, '--profile', profile, 'up', '-d' ], capture_output=True, text=True )
    if p.returncode == 0: 
        print(p.stdout)
    else:
        print("error")

def upRecreate(profile):
    p = subprocess.run( [ 'docker', 'compose', '--env-file', envFile, '--profile', profile, 'up', '--force-recreate', '-d' ], capture_output=True, text=True )
    if p.returncode == 0: 
        print(p.stdout)
    else:
        print("error")

def readConfigValue(key):
    return get_key(envFile, key)

def updateConfigValue(key, value):
    #success, key, value = set_key(file, key, value, quote, export)
    return set_key(envFile, key, value, 'never', false)
