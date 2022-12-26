#!/usr/bin/python3

import subprocess
from dotenv.main import get_key, set_key
import os
import date

envFile = "/etc/opt/compose/.env"

backupFiles [
    '/etc/opt/compose/.env',
    '/etc/opt/squeezelite',
    '/etc/opt/eq',
    '/var/lib/alsa/asound.state'
]

backupTempName = "/tmp/backup.tar.gz"

def createLocalBackup():
    p = subprocess.run( [ 'tar', '-czf', backupTempName ] + backupFiles, capture_output=True, text=True )
    if p.returncode == 0: 
        print(p.stdout)
    else:
        print("error")

def copyBackupToRemote():
    remoteHost = get_key(envFile, "BACKUP_SSH_USER") + "@" + get_key(envFile, "BACKUP_SSH_HOST")
    remoteFileName = get_key(envFile, "BACKUP_REMOTE_DIRECTORY") + "/" + time.strftime("%Y%m%d-%H%M%S") + ".tar.gz"
    cmd = [ 'sshpass', '-p', get_key(envFile, "BACKUP_SSH_PASSWORD"), 
        'scp', '-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null',
        '-P', get_key(envFile, "BACKUP_SSH_PORT"), backupTempName, remoteHost + ":" + remoteFileName)]
    p = subprocess.run( cmd, capture_output=True, text=True )
    if p.returncode == 0: 
        print(p.stdout)
    else:
        print("error")

def deleteLocalBackup():
    if os.path.exists(backupTempName):
        os.remove(backupTempName)
    else:
        print("backup file does not exist")