#!/usr/bin/python3

import asyncio
from dotenv.main import get_key, set_key

envFile = "/etc/opt/compose/.env"

# created, restarting, running, removing, paused, exited and dead
async def getContainerStatus():
    program = [ 'docker', 'ps', '--format', '{{.Names}}:{{.State}}' ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        return extractContainerStatus(stdout.decode())
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

async def up(profile, recreate=False):
    program = [ 'docker', 'compose', '--env-file', envFile, '--profile', profile, 'up', '--detach' ]
    if recreate:
        programm.append('--force-recreate')
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        print(stdout.decode())
        print(stderr.decode())
    else:
        print("error")

def readConfigValue(key):
    return get_key(envFile, key)

def updateConfigValue(key, value):
    #success, key, value = set_key(file, key, value, quote, export)
    return set_key(envFile, key, value, 'never', false)

async def main():
    print('compose test')

    print (await getContainerStatus())
    await up('on')

if __name__ == '__main__':
    asyncio.run(main())
