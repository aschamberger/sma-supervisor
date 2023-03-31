#!/usr/bin/python3

import asyncio

async def alsactl_store():
    program = [ 'alsactl', 'store' ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        return stdout
    else:
        print("error")

async def get_equalizer(channel):
    device = f"ch{channel}_eq"
    # amixer -D ch1_eq scontents
    program = [ 'amixer', '-D', device, 'scontents' ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        return extract_equalizer_settings(stdout.decode())
    else:
        print("error")

async def set_equalizer(channel, settings):
    commands = ("sset '00. 31 Hz' " + settings[0] + "\n"
    "sset '01. 63 Hz' " + settings[1] + "\n"
    "sset '02. 125 Hz' " + settings[2] + "\n"
    "sset '03. 250 Hz' " + settings[3] + "\n"
    "sset '04. 500 Hz' " + settings[4] + "\n"
    "sset '05. 1 kHz' " + settings[5] + "\n"
    "sset '06. 2 kHz' " + settings[6] + "\n"
    "sset '07. 4 kHz' " + settings[7] + "\n"
    "sset '08. 8 kHz' " + settings[8] + "\n"
    "sset '09. 16 kHz' " + settings[9])

    device = f"ch{channel}_eq"
    # amixer -D ch1_eq sset '00. 31 Hz' 66
    # amixer -D ch1_eq -s < stdin
    program = [ 'amixer', '-D', device, '-s' ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE, stdin=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate(commands.encode())
    if p.returncode == 0:
        return extract_equalizer_settings(stdout.decode())
    else:
      print("error")

async def set_equalizer_channel(channel, eq_channel, setting):
    settings = ['0+', '0+', '0+', '0+', '0+', '0+', '0+', '0+', '0+', '0+']
    settings[eq_channel] = setting
    result = await set_equalizer(channel, settings)
    return result

def extract_equalizer_settings(result):
    lines = result.split("\n")
    settings = [lines[5].split()[4][1:-2],
        lines[12].split()[4][1:-2],
        lines[19].split()[4][1:-2],
        lines[26].split()[4][1:-2],
        lines[33].split()[4][1:-2],
        lines[40].split()[4][1:-2],
        lines[47].split()[4][1:-2],
        lines[54].split()[4][1:-2],
        lines[61].split()[4][1:-2],
        lines[68].split()[4][1:-2]]
    return settings

async def get_all_device_volumes():
    cardA = await get_device_volumes("hw:CARD=SND_A")
    cardB = await get_device_volumes("hw:CARD=SND_B")
    volumes = [cardA[0],
        cardA[2],
        cardA[4],
        cardA[6],
        cardB[0],
        cardB[2],
        cardB[4],
        cardB[6]]
    return volumes

async def get_device_volumes(device):
    # amixer -D hw:CARD=SND_A get Speaker
    # -M Use the mapped volume for evaluating the percentage representation like alsamixer, to be more natural for human ear.
    # command returs same result as the 'get' command
    program = [ 'amixer', '-D', device, '-M', 'get', 'Speaker' ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
      return extract_volume_settings(stdout.decode())
    else:
      print("error")

async def set_channel_volume(channel, volume):
    channel = int(channel)
    # ch1 | ch4 | ch3 | ch2
    # ch5 | ch8 | ch7 | ch6
    volumes = ['0%+', '0%+', '0%+', '0%+', '0%+', '0%+', '0%+', '0%+']
    if channel == 1 or channel == 5:
      volumes[0] = f"{volume}%"
      volumes[1] = f"{volume}%"
      returnIndex = 0
    elif channel == 4 or channel == 8:
      volumes[2] = f"{volume}%"
      volumes[3] = f"{volume}%"
      returnIndex = 2
    elif channel == 3 or channel == 7:
      volumes[4] = f"{volume}%"
      volumes[5] = f"{volume}%"
      returnIndex = 4
    elif channel == 2 or channel == 6:
      volumes[6] = f"{volume}%"
      volumes[7] = f"{volume}%"
      returnIndex = 6
    set_volume = ",".join(volumes)

    if channel >= 1 and channel <= 4:
      device = "hw:CARD=SND_A"
    elif channel >= 5 and channel <= 8:
      device = "hw:CARD=SND_B"

    # amixer -D hw:CARD=SND_A -M set Speaker <volume>
    # amixer -D hw:CARD=SND_A -M set Speaker 65%,66%,67%,68%,69%,70%,71%,72%
    # -M Use the mapped volume for evaluating the percentage representation like alsamixer, to be more natural for human ear.
    # command returs same result as the 'get' command
    program = [ 'amixer', '-D', device, '-M', 'set', 'Speaker', set_volume ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        volumes = extract_volume_settings(stdout.decode())
        return volumes[returnIndex]
    else:
        print("error")

def extract_volume_settings(result):
    lines = result.split("\n")
    equal = [lines[5].split()[4][1:-2],
        lines[6].split()[4][1:-2],
        lines[7].split()[4][1:-2],
        lines[8].split()[4][1:-2],
        lines[9].split()[4][1:-2],
        lines[10].split()[3][1:-2],
        lines[11].split()[4][1:-2],
        lines[12].split()[4][1:-2]]
    return equal

async def main():
    print('alsa control test')

    channel = 1
    equal = ['66', '66', '66', '66', '66', '66', '66', '66', '66', '66']

    print(await get_equalizer(channel))
    print(await set_equalizer(channel, equal))
    print(await get_all_device_volumes())
    print(await set_channel_volume(channel, '7'))

if __name__ == '__main__':
    asyncio.run(main())