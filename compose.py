#!/usr/bin/python3

import subprocess
from dotenv.main import get_key, set_key

envFile = "/etc/opt/compose/.env"
composeFile = "/usr/local/src/sma/compose.yml"

def up():
    p = subprocess.run( [ 'docker-compose', '-f', composeFile, '--env-file', envFile, '--profile', 'on', 'up', '-d' ], capture_output=True, text=True )
    if p.returncode == 0: 
        print(p.stdout)
    else:
        print("error")

def upRecreate():
    p = subprocess.run( [ 'docker-compose', '-f', composeFile, '--env-file', envFile, '--profile', 'on', 'up', '--force-recreate', '-d' ], capture_output=True, text=True )
    if p.returncode == 0: 
        print(p.stdout)
    else:
        print("error")

def readConfigValue(key):
    return get_key(envFile, key)

def updateConfigValue(key, value):
    #success, key, value = set_key(file, key, value, quote, export)
    return set_key(envFile, key, value, 'never', false)
