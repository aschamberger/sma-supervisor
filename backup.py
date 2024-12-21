#!/usr/bin/python3

import asyncio
from dotenv.main import get_key, set_key
import os
import time

envFile = "/etc/opt/compose/.env"

backupFiles = [
    '/etc/opt/compose/.env',
    '/etc/opt/squeezelite',
    '/etc/opt/eq',
    '/var/lib/alsa/asound.state'
]

backupTempName = "/tmp/backup.tar.gz"

async def create_local_backup():
    program = [ 'tar', '-czf', backupTempName ] + backupFiles
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        out = stdout.decode()
        if "removing leading '/' from member names" not in out:
            print(out)
    else:
        print("error")

async def copy_backup_to_remote():
    remoteHost = get_key(envFile, "BACKUP_SSH_USER") + "@" + get_key(envFile, "BACKUP_SSH_HOST")
    remoteFileName = get_key(envFile, "BACKUP_SSH_FOLDER") + "/" + time.strftime("%Y%m%d-%H%M%S") + ".tar.gz"
    program = [ 'sshpass', '-p', get_key(envFile, "BACKUP_SSH_PASSWORD"),
        'scp', '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null',
        '-P', get_key(envFile, "BACKUP_SSH_PORT"), backupTempName, remoteHost + ":" + remoteFileName]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        out = stdout.decode()
        if "Permanently added" not in out:
            print(out)
    else:
        print("error")

def delete_local_backup():
    if os.path.exists(backupTempName):
        os.remove(backupTempName)
    else:
        print("backup file does not exist")

async def main():
    print('backup test')

    await create_local_backup()
    await copy_backup_to_remote()
    delete_local_backup()

if __name__ == '__main__':
    asyncio.run(main())