# Supervisor Docker

Supervisor docker to control the squeezeMultiAmp via MQTT from [Home Assistant](https://www.home-assistant.io/). 

Features:
* control server, alsa sound level, equalizer, ...
* based on Alpine Linux
* Container init via [Tini](https://github.com/krallin/tini)
* rootless via [su-exec](https://github.com/ncopa/su-exec)
* supports [alsaequal](https://github.com/raedwulf/alsaequal)

Configuration/control options:
* server shutdown/restart
* restart all squeezlite/hermes containers
* backup and upload all custom config (player names, eq/volume settings, env-file) via scp to other host
* equalizer settings
* channel volume settings
* change names of squeezelite players (can also be done via LMS interface)
* set up external home assistant switch entity per channel
* set up LMS, MQTT, Home Assistant hostnames/IPs
* set up Home Assistant bearer token

Not configurable via supervisor:
* GPIOs --> edit env file and container restart required
* enable/disable player or hermes instances --> edit env file and container restart required

## Docker build

```
sudo docker build -t supervisor .
```

## Docker run

...

## Docker dev

Run and login to shell:
```
sudo docker run -it --network host --device /dev/gpiomem --device /dev/snd --ipc="host" supervisor /bin/sh
```
Login to running container:
```
sudo docker exec -it supervisor /bin/sh
```
Supervisor source code volume from host:
```
cd /usr/local/src/sma/supervisor
```

## Notes/links

### MQTT and HA discovery

Links:
* https://github.com/sbtinstruments/asyncio-mqtt
* https://sbtinstruments.github.io/asyncio-mqtt/sharing-the-connection.html
* https://www.home-assistant.io/docs/mqtt/discovery/

### Server shutdown/restart

squeezelite players are stopped before restart/shutdown to prevent plops.

Implementation note on pysqueezebox usage: the player object is not used as the name attribute is cached and needs to be refreshed anyways. Also the creating of the object is only possible when the player is already connected to the LMS.

Links:
* https://fhackts.wordpress.com/2019/08/08/shutting-down-or-rebooting-over-dbus-programmatically-from-a-non-root-user/
* https://github.com/Bluetooth-Devices/dbus-fast
* https://stackoverflow.com/questions/59434149/using-dbus-to-poweroff-raspberry-pi-inside-docker-container-and-python
* https://github.com/rajlaud/pysqueezebox 

### Restart squeezlite/hermes containers

You can't restart the supervisor but only the other containers because when the container is shut down the compose restart command would also be killed.

### Backup and upload all config via scp to other host

As 255 is the maximum number of characters allowed in an Home Assistant entity state it was not possible to store a ssh key.
So backup is done via user auth using https://pkgs.alpinelinux.org/packages?name=sshpass&branch=edge&repo=&arch=&maintainer=

### Equalizer settings / Channel volume settings

`amixer/alsactl` is run via subprocess calls. Relative values (0+, 0%+) are used to selectivly set values and keep the others unchanged.

Links:
* https://docs.python.org/3/library/asyncio-subprocess.html#asyncio-subprocess
* https://csatlas.com/python-subprocess-run-exec-system-command/
* does not seem to support equalizer at first impression: http://larsimmisch.github.io/pyalsaaudio/libalsaaudio.html

### Ideas that most likely won't be realized

* https://github.com/skiffos/skiffos + GitHub actions + https://www.home-assistant.io/integrations/update.mqtt
* usb restart via uhubctl (network down required for usb restart? org.freedesktop.NetworkManager via dbus?) >> withdrawn as with current USB HUB the USB seems to be stable