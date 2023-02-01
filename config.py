#!/usr/bin/python3

import re, uuid

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
        'topic': "homeassistant/text/sma_lms_host/config",
        'payload':
        {
            "name": "sMA Logitech Media Server Host",
            "description": "Format: host:port",
            "device": device,
            "entity_category": "config",
            "icon": "mdi:server-network",
            "cmd_t": "homeassistant/text/sma_lms_host/set",
            "stat_t": "homeassistant/text/sma_lms_host/state"
        }
    },
    {
        'topic': "homeassistant/text/sma_mqtt_host/config",
        'payload':
        {
            "name": "sMA MQTT Host",
            "description": "Format: host:port",
            "device": device,
            "entity_category": "config",
            "icon": "mdi:server-network",
            "cmd_t": "homeassistant/text/sma_mqtt_host/set",
            "stat_t": "homeassistant/text/sma_mqtt_host/state"
        }
    },
    {
        'topic': "homeassistant/text/sma_hass_host/config",
        'payload':
        {
            "name": "sMA Home Assistant Host",
            "description": "Format: host:port",
            "device": device,
            "entity_category": "config",
            "icon": "mdi:server-network",
            "cmd_t": "homeassistant/text/sma_hass_host/set",
            "stat_t": "homeassistant/text/sma_hass_host/state"
        }
    },
    {
        'topic': "homeassistant/text/sma_hass_bearer/config",
        'payload':
        {
            "name": "sMA Home Assistant bearer token",
            "device": device,
            "entity_category": "config",
            "icon": "mdi:lock",
            "mode": "password",
            "cmd_t": "homeassistant/text/sma_hass_bearer/set",
            "stat_t": "homeassistant/text/sma_hass_bearer/state"
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

# subdevice: sqeezeMultiAmp Channel #?
for channel in range(1, 9):
    channel = "{:02d}".format(channel)
    subdevice = {
        "name": "sqeezeMultiAmp Channel #" + channel,
        "identifiers": "02:00:00:00:00:" + channel,
        "via_device": mac
    }

    entities += [
        {
            'topic': "homeassistant/binary_sensor/sma_channel_" + channel + "/config",
            'payload':
            {
                "name": "sMA Channel #" + channel + " State",
                "device": subdevice,
                "entity_category": "diagnostic",
                "dev_cla": "running",
                "stat_t": "homeassistant/binary_sensor/sma_channel_" + channel + "/state"
            }
        },
        {
            'topic': "homeassistant/text/sma_channel_" + channel + "_player_name/config",
            'payload':
            {
                "name": "sMA Channel #" + channel + " Player Name",
                "device": subdevice,
                "entity_category": "config",
                "icon": "mdi:rename",
                "dev_cla": "running",
                "cmd_t": "homeassistant/text/sma_channel_" + channel + "_player_name/set",
                "stat_t": "homeassistant/text/sma_channel_" + channel + "_player_name/state"
            }
        }
    ]

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

    entities += [
        {
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
        },
        {
            'topic': "homeassistant/text/sma_channel_" + channel + "_hass_switch/config",
            'payload':
            {
                "name": "sMA Channel #" + channel + " External Switch",
                "description": "Home Assistant entity id that should be switched on/off based on player state",
                "device": subdevice,
                "entity_category": "config",
                "icon": "mdi:electric-switch",
                "cmd_t": "homeassistant/text/sma_channel_" + channel + "_hass_switch/set",
                "stat_t": "homeassistant/text/sma_channel_" + channel + "_hass_switch/state"
            }
        }
    ]