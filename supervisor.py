#!/usr/bin/python3

import sys
import os
import argparse
import time
import paho.mqtt.client as mqtt
import io
from zeroconf import ServiceBrowser, Zeroconf
import re, uuid
from LMSTools import LMSDiscovery, LMSServer, LMSPlayer

import json

import alsa
import dbus
import compose

# TODO/ideas
# TODO reboot or shutdown only after shutdown audio to prevent plopp
# TODO set eq/scene enables eq if not enabled
# https://www.home-assistant.io/integrations/update.mqtt




_RUNNING = True

eqChannels = ["00. 31 Hz",
    "01. 63 Hz",
    "02. 125 Hz",
    "03. 250 Hz",
    "04. 500 Hz",
    "05. 1 kHz",
    "06. 2 kHz",
    "07. 4 kHz",
    "08. 8 kHz",
    "09. 16 kHz"]
# equalizer range is from 36 to 95
eqPresets = {
    "flat": ['66', '66', '66', '66', '66', '66', '66', '66', '66', '66'],
    "classic": ['78', '70', '67', '63', '58', '60', '64', '69', '78', '76'],
    "rock": ['76', '78', '75', '70', '67', '72', '72', '72', '69', '69'],
    "loud": ['76', '76', '73', '67', '67', '67', '67', '55', '75', '76'],
    "pop": ['79', '75', '70', '67', '64', '72', '70', '73', '76', '79']
}




channel = 'ch1'
equal = ['66', '66', '66', '66', '66', '66', '66', '66', '66', '66']

print(alsa.getEqualizer(channel))
print(alsa.setEqualizer(channel, equal))
print(alsa.getAllDeviceVolumes())
print(alsa.setChannelVolume(channel, '75'))





def onConnect(client, userdata, flags, rc):
    print("Connected to mqtt server with result code " + str(rc))

    mac = ':'.join(re.findall('..', '%012x' % uuid.getnode())) # mac address

    device = {
        "name": "sqeezeMultiAmp",
        "identifiers": mac
    }

    # set up home assisstant entities
    # device: sqeezeMultiAmp
    entities = [
        {
            'topic': "homeassistant/binary_sensor/sma_supervisor/config",
            'payload':
            {
                "name": "sMA Supervisor State",
                "device": device,
                "entity_category": "diagnostic",
                "dev_cla": "running",
                "stat_t": "homeassistant/binary_sensor/sma_supervisor/state"
            }
        },
        {
            'topic': "homeassistant/button/sma_shutdown/config",
            'payload':
            {
                "name": "sMA Server Shutdown",
                "device": device,
                "entity_category": "config",
                "dev_cla": "None",
                "icon": "mdi:stop",
                "cmd_t": "homeassistant/button/sma_shutdown/do"
            }
        },
        {
            'topic': "homeassistant/button/sma_restart/config",
            'payload':
            {
                "name": "sMA Server Restart",
                "device": device,
                "entity_category": "config",
                "dev_cla": "restart",
                "icon": "mdi:restart",
                "cmd_t": "homeassistant/button/sma_restart/do"
            }
        },
        {
            'topic': "homeassistant/button/sma_compose_recreate/config",
            'payload':
            {
                "name": "sMA Container Recreate",
                "device": device,
                "entity_category": "config",
                "dev_cla": "restart",
                "icon": "mdi:autorenew",
                "cmd_t": "homeassistant/button/sma_compose_recreate/do"
            }
        },
        {
            'topic': "homeassistant/button/sma_usb_restart/config",
            'payload':
            {
                "name": "sMA USB Restart",
                "device": device,
                "entity_category": "config",
                "dev_cla": "restart",
                "icon": "mdi:usb",
                "cmd_t": "homeassistant/button/sma_usb_restart/do"
            }
        },
        {
            'topic': "homeassistant/button/sma_remote_backup/config",
            'payload':
            {
                "name": "sMA Remote Backup ",
                "device": device,
                "entity_category": "config",
                "icon": "mdi:cloud-upload",
                "cmd_t": "homeassistant/button/sma_remote_backup/do"
            }
        },
        {
            'topic': "homeassistant/text/sma_backup_host/config",
            'payload':
            {
                "name": "sMA Remote Backup Host",
                "description": "Format: user@host:port",
                "device": device,
                "entity_category": "config",
                "icon": "mdi:server-network",
                "cmd_t": "homeassistant/text/sma_backup_host/set",
                "stat_t": "homeassistant/text/sma_backup_host/state"
            }
        },
        {
            'topic': "homeassistant/text/sma_backup_password/config",
            'payload':
            {
                "name": "sMA Remote Backup Password",
                "device": device,
                "entity_category": "config",
                "icon": "mdi:lock",
                "mode": "password",
                "cmd_t": "homeassistant/text/sma_backup_password/set",
                "stat_t": "homeassistant/text/sma_backup_password/state"
            }
        },
        {
            'topic': "homeassistant/text/sma_backup_folder/config",
            'payload':
            {
                "name": "sMA Remote Backup Folder",
                "device": device,
                "entity_category": "config",
                "icon": "mdi:folder",
                "cmd_t": "homeassistant/text/sma_backup_folder/set",
                "stat_t": "homeassistant/text/sma_backup_folder/state"
            }
        },
        # {
            # 'topic': "homeassistant/number/sma_gpio_relay/config",
            # 'payload':
            # {
                # "name": "sMA GPIO Relay",
                # "device": device,
                # "entity_category": "config",
                # "icon": "mdi:power-plug",
                # "cmd_t": "homeassistant/number/sma_gpio_relay/set",
                # "stat_t": "homeassistant/number/sma_gpio_relay/state",
                # "min": 1,
                # "max": 26
            # }
        # }
    ]

    for channel in range(1, 10):
        channel = "{:02d}".format(channel)
        subdevice = {
            "name": "sqeezeMultiAmp Channel #" + channel,
            "identifiers": "02:00:00:00:00:" + channel,
            "via_device": mac
        }

        entities.append({
            'topic': "homeassistant/binary_sensor/sma_channel_" + channel + "/config",
            'payload':
            {
                "name": "sMA Channel #" + channel + " State",
                "device": subdevice,
                "entity_category": "diagnostic",
                "dev_cla": "running",
                "stat_t": "homeassistant/binary_sensor/sma_channel_" + channel + "/state"
            }
        })

        entities.append({
            'topic': "homeassistant/text/sma_channel_" + channel + "_player_name/config",
            'payload':
            {
                "name": "sMA Channel #" + channel + " Player Name",
                "device": subdevice,
                "entity_category": "diagnostic",
                "dev_cla": "running",
                "stat_t": "homeassistant/text/sma_channel_" + channel + "_player_name/state"
            }
        })

        for eqChannel in eqChannels:
            entities.append({
                'topic': "homeassistant/number/sma_channel_" + channel + "_eq_" + eqChannel[:2] + "/config",
                'payload':
                {
                    "name": "sMA Channel #" + channel + " EQ " + eqChannel,
                    "device": subdevice,
                    "entity_category": "config",
                    "icon": "mdi:tune",
                    "cmd_t": "homeassistant/number/sma_channel_" + channel + "_eq_" + eqChannel[:2] + "/set",
                    "stat_t": "homeassistant/number/sma_channel_" + channel + "_eq_" + eqChannel[:2] + "/state",
                    "min": 36,
                    "max": 95
                }
            })

        for eqPreset in eqPresets.keys():
            entities.append({
                'topic': "homeassistant/scene/sma_channel_" + channel + "_eq_preset_" + eqPreset + "/config",
                'payload':
                {
                    "name": "sMA Channel #" + channel + " EQ preset " + eqPreset,
                    "device": subdevice,
                    "dev_cla": "None",
                    "icon": "mdi:folder-star",
                    "cmd_t": "homeassistant/scene/sma_channel_" + channel + "_eq_" + eqPreset + "/set",
                    "pl_on": eqPreset
                }
            })

        entities.append({
            'topic': "homeassistant/number/sma_channel_" + channel + "_volume/config",
            'payload':
            {
                "name": "sMA Channel #" + channel + " volume",
                "device": subdevice,
                "entity_category": "config",
                "icon": "mdi:volume-high",
                "cmd_t": "homeassistant/number/sma_channel_" + channel + "_volume/set",
                "stat_t": "homeassistant/number/sma_channel_" + channel + "_volume/state",
                "min": 0,
                "max": 100
            }
        })

    pretty = json.dumps(entities, indent=4)
    print(pretty)


    # publish entities for mqtt discovery and subscribe to their topics
    for entity in entities:
        # client.publish(entity['topic'], payload=entity['payload'], retain=True)
        if entity['payload']['cmd_t']:
            # client.subscribe(entity['payload']['cmd_t'])
        if entity['payload']['stat_t']:
            # client.subscribe(entity['payload']['stat_t'])

#def playFinished(client, userdata, msg):
#    print(msg.topic)

def stop():
    global _RUNNING
    _RUNNING = False

def find_service(self, zeroconf, service_type, name, state_change):
    info = zeroconf.get_service_info(service_type, name)
    #if not (info.port == 1883 and service_type == "_mqtt._tcp.local."):
    if not (service_type == "_mqtt._tcp.local."):
        return

    if state_change is ServiceStateChange.Added:
        mqttHost[0] = str(socket.inet_ntoa(info.address))
        mqttHost[1] = info.port
    elif state_change is ServiceStateChange.Removed:
        pass

if __name__ == '__main__':
    print('Starting supervisor')

    if os.getenv('MQTT_HOST') is not None:
        mqttHost = os.getenv('MQTT_HOST').split(':')
        if len(mqttHost) == 1:
            mqttHost.append(1883)
    else:
        zeroconf = Zeroconf()
        browser = ServiceBrowser(zeroconf, "_mqtt._tcp.local.", handlers=[find_service])
        time.sleep(5)
        zeroconf.close()
        if not(mqttHost[0]):
            sys.exit('No mqtt broker could be discovered via zeroconf and no config given manually')
        else:
            compose.updateConfigValue('MQTT_HOST', ':'.join(mqttHost))

    if os.getenv('LMS_HOST') is None:
        servers = LMSDiscovery().all()
        lmsHost = [servers[0]['host'], servers[0]['port']]
        if len(servers) == 0:
            sys.exit('No Logitech Media Server could be discovered and no config given manually')
        else:
            compose.updateConfigValue('LMS_HOST', ':'.join(lmsHost))

    mqttClient = mqtt.Client()
    mqttClient.on_connect = onConnect
    mqttClient.message_callback_add("hermes/audioServer/{}/playBytes/#".format(args.siteId), playBytes)
#    mqttClient.message_callback_add("hermes/audioServer/{}/playFinished/#".format(args.siteId), playFinished)
    mqttClient.connect(mqttHost[0], int(mqttHost[1]))
    mqttClient.loop_start()

    try:
        while _RUNNING:
            time.sleep(0.1)
        raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass
    finally:
        mqttClient.loop_stop()