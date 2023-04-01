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
* equalizer settings [RESTART if not previously chX_eq configured - which is default]
* channel volume settings
* change names of squeezelite players (can also be done via LMS interface)
* set up external home assistant switch entity per channel [RESTART]
* set up LMS, MQTT, Home Assistant hostnames/IPs [RESTART]
* set up Home Assistant bearer token [RESTART]
[RESTART] = squeezelite containers are recreated/restarted to pick up changes

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

### Install local mosquitto broker for testing

```
sudo apt install mosquitto mosquitto-clients
mosquitto_sub -h 127.0.0.1 -v -t "homeassistant/#"
```

#### Setting values from MQTT

```
mosquitto_pub -h 127.0.0.1 -t "homeassistant/number/smab827eb6d35a8/smab827eb6d35a8_ch08_volume/set" -m 29
mosquitto_pub -h 127.0.0.1 -t "homeassistant/number/smab827eb6d35a8/smab827eb6d35a8_ch08_eq00_eqsetting/set" -m 75

mosquitto_pub -h 127.0.0.1 -t "homeassistant/scene/smab827eb6d35a8/smab827eb6d35a8_ch08_eqpreset/set" -m "pop"

mosquitto_pub -h 127.0.0.1 -t "homeassistant/button/smab827eb6d35a8/smab827eb6d35a8_shutdown/do" -m ON
mosquitto_pub -h 127.0.0.1 -t "homeassistant/button/smab827eb6d35a8/smab827eb6d35a8_restart/do" -m ON
mosquitto_pub -h 127.0.0.1 -t "homeassistant/button/smab827eb6d35a8/smab827eb6d35a8_remote_backup/do" -m ON
mosquitto_pub -h 127.0.0.1 -t "homeassistant/button/smab827eb6d35a8/smab827eb6d35a8_compose_recreate/do" -m ON

mosquitto_pub -h 127.0.0.1 -t "homeassistant/text/smab827eb6d35a8/smab827eb6d35a8_ch08_player_name/set" -m "Werkraum-Test123"

mosquitto_pub -h 127.0.0.1 -t "homeassistant/text/smab827eb6d35a8/smab827eb6d35a8_ch08_hass_switch/set" -m "switch.sound_werkraum_switch"
mosquitto_pub -h 127.0.0.1 -t "homeassistant/text/smab827eb6d35a8/smab827eb6d35a8_backup_host/set" -m "backup@192.168.178.x:22"
mosquitto_pub -h 127.0.0.1 -t "homeassistant/text/smab827eb6d35a8/smab827eb6d35a8_backup_password/set" -m "PW123"
mosquitto_pub -h 127.0.0.1 -t "homeassistant/text/smab827eb6d35a8/smab827eb6d35a8_backup_folder/set" -m "/mnt/user/appdata/..."

mosquitto_pub -h 127.0.0.1 -t "homeassistant/text/smab827eb6d35a8/smab827eb6d35a8_hass_bearer/set" -m "eyJ...."
mosquitto_pub -h 127.0.0.1 -t "homeassistant/text/smab827eb6d35a8/smab827eb6d35a8_lms_host/set" -m "192.168.178.x:9000"
mosquitto_pub -h 127.0.0.1 -t "homeassistant/text/smab827eb6d35a8/smab827eb6d35a8_mqtt_host/set" -m "localhost:1883"
mosquitto_pub -h 127.0.0.1 -t "homeassistant/text/smab827eb6d35a8/smab827eb6d35a8_hass_host/set" -m "192.168.178.x:8123"
```

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
* old polkit does not have javascript rules: 
  - https://unix.stackexchange.com/a/417968 
  - https://unix.stackexchange.com/a/491603
  - https://unix.stackexchange.com/questions/289123/explanation-of-file-org-freedesktop-login1-policy
  - check ploicy `pkcheck --action-id org.freedesktop.login1.reboot --process $$ -u; echo $?`
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

### Ideas for the future

* limit container restarts if too many/multiple commands resulting in restarts --> queue tasks and consolidate
* limit permissions to supervisor for reboot and do not grant for all users --> create a supervisor user and map to container: https://docs.docker.com/engine/reference/run/#user
* better file permissions handling in setup
* https://github.com/skiffos/skiffos + GitHub actions + https://www.home-assistant.io/integrations/update.mqtt
* usb restart via uhubctl (network down required for usb restart? org.freedesktop.NetworkManager via dbus?) >> withdrawn as with current USB HUB the USB seems to be stable