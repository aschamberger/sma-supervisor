#!/usr/bin/python3

import re, uuid

num_channels = 8

lms_players = []
for channel in range(1, num_channels+1):
    lms_players.append(f"02:00:00:00:00:{channel:02d}")

eq_channels = ["00. 31 Hz",
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
eq_presets = {
    "flat": ['66', '66', '66', '66', '66', '66', '66', '66', '66', '66'],
    "classic": ['78', '70', '67', '63', '58', '60', '64', '69', '78', '76'],
    "rock": ['76', '78', '75', '70', '67', '72', '72', '72', '69', '69'],
    "loud": ['76', '76', '73', '67', '67', '67', '67', '55', '75', '76'],
    "pop": ['79', '75', '70', '67', '64', '72', '70', '73', '76', '79']
}

discovery_prefix = "homeassistant"
node_id = f"sma{''.join(re.findall('..', '%012x' % uuid.getnode()))}"

subscriptions = [
    f"{discovery_prefix}/+/{node_id}/+/do",
    f"{discovery_prefix}/+/{node_id}/+/set"
]

device = {
    "name": "sqeezeMultiAmp",
    "identifiers": [node_id]
}

# set up home assisstant entities
# device: sqeezeMultiAmp
entities = [
    {
        "~": f"{discovery_prefix}/binary_sensor/{node_id}/{node_id}_supervisor",
        "unique_id": f"{node_id}_supervisor",
        "name": "sMA Supervisor Container State",
        "object_id": f"{node_id}_supervisor",
        "device": device,
        "entity_category": "diagnostic",
        "dev_cla": "running",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/button/{node_id}/{node_id}_shutdown",
        "unique_id": f"{node_id}_shutdown",
        "name": "sMA Server Shutdown",
        "object_id": f"{node_id}_shutdown",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:stop",
        "cmd_t": "~/do"
    },
    {
        "~": f"{discovery_prefix}/button/{node_id}/{node_id}_restart",
        "unique_id": f"{node_id}_restart",
        "name": "sMA Server Restart",
        "object_id": f"{node_id}_restart",
        "device": device,
        "entity_category": "config",
        "dev_cla": "restart",
        "icon": "mdi:restart",
        "cmd_t": "~/do"
    },
    {
        "~": f"{discovery_prefix}/button/{node_id}/{node_id}_compose_recreate",
        "unique_id": f"{node_id}_compose_recreate",
        "name": "sMA Container Recreate",
        "object_id": f"{node_id}_compose_recreate",
        "device": device,
        "entity_category": "config",
        "dev_cla": "restart",
        "icon": "mdi:autorenew",
        "cmd_t": "~/do"
    },
    {
        "~": f"{discovery_prefix}/text/{node_id}/{node_id}_lms_host",
        "unique_id": f"{node_id}_lms_host",
        "name": "sMA Logitech Media Server Host",
        "object_id": f"{node_id}_lms_host",
        "description": "Format: host:port",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:server-network",
        "cmd_t": "~/set",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/text/{node_id}/{node_id}_mqtt_host",
        "unique_id": f"{node_id}_mqtt_host",
        "name": "sMA MQTT Host",
        "object_id": f"{node_id}_mqtt_host",
        "description": "Format: [user@]host:port (user is optional)",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:server-network",
        "cmd_t": "~/set",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/text/{node_id}/{node_id}_mqtt_password",
        "unique_id": f"{node_id}_mqtt_password",
        "name": "sMA MQTT Password",
        "object_id": f"{node_id}_mqtt_password",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:lock",
        "mode": "password",
        "cmd_t": "~/set",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/text/{node_id}/{node_id}_hass_host",
        "unique_id": f"{node_id}_hass_host",
        "name": "sMA Home Assistant Host",
        "object_id": f"{node_id}_hass_host",
        "description": "Format: host:port",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:server-network",
        "cmd_t": "~/set",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/text/{node_id}/{node_id}_hass_bearer",
        "unique_id": f"{node_id}_hass_bearer",
        "name": "sMA Home Assistant bearer token",
        "object_id": f"{node_id}_hass_bearer",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:lock",
        "mode": "password",
        "cmd_t": "~/set",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/button/{node_id}/{node_id}_remote_backup",
        "unique_id": f"{node_id}_remote_backup",
        "name": "sMA Remote Backup ",
        "object_id": f"{node_id}_remote_backup",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:cloud-upload",
        "cmd_t": "~/do"
    },
    {
        "~": f"{discovery_prefix}/text/{node_id}/{node_id}_backup_host",
        "unique_id": f"{node_id}_backup_host",
        "name": "sMA Remote Backup Host",
        "object_id": f"{node_id}_backup_host",
        "description": "Format: user@host:port",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:server-network",
        "cmd_t": "~/set",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/text/{node_id}/{node_id}_backup_password",
        "unique_id": f"{node_id}_backup_password",
        "name": "sMA Remote Backup Password",
        "object_id": f"{node_id}_backup_password",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:lock",
        "mode": "password",
        "cmd_t": "~/set",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/text/{node_id}/{node_id}_backup_folder",
        "unique_id": f"{node_id}_backup_folder",
        "name": "sMA Remote Backup Folder",
        "object_id": f"{node_id}_backup_folder",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:folder",
        "cmd_t": "~/set",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/text/{node_id}/{node_id}_gpio_psu_relay",
        "unique_id": f"{node_id}_gpio_psu_relay",
        "name": "sMA GPIO Power Supply Relay",
        "object_id": f"{node_id}_gpio_psu_relay",
        "description": "GPIO physical pin number (1-40)",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:power-plug",
        "cmd_t": "~/set",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/text/{node_id}/{node_id}_gpio_mute",
        "unique_id": f"{node_id}_gpio_mute",
        "name": "sMA GPIO Channel Mute",
        "object_id": f"{node_id}_gpio_mute",
        "description": "List of GPIO physical pin numbers (1-40)",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:volume-mute",
        "cmd_t": "~/set",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/text/{node_id}/{node_id}_gpio_sps",
        "unique_id": f"{node_id}_gpio_sps",
        "name": "sMA GPIO Speaker Switch",
        "object_id": f"{node_id}_gpio_sps",
        "description": "List of GPIO physical pin numbers (1-40)",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:ab-testing",
        "cmd_t": "~/set",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/update/{node_id}/{node_id}_update_supervisor",
        "unique_id": f"{node_id}_update_supervisor",
        "name": "sMA Update Supervisor",
        "object_id": f"{node_id}_update_supervisor",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:oci",
        "cmd_t": "~/do",
        "stat_t": "~/state"
    },
    {
        "~": f"{discovery_prefix}/update/{node_id}/{node_id}_update_squeezelite",
        "unique_id": f"{node_id}_update_squeezelite",
        "name": "sMA Update Supervisor",
        "object_id": f"{node_id}_update_squeezelite",
        "device": device,
        "entity_category": "config",
        "icon": "mdi:oci",
        "cmd_t": "~/do",
        "stat_t": "~/state"
    }
]

# subdevice: sqeezeMultiAmp Channel #?
for channel in range(1, num_channels+1):
    channel = f"{channel:02d}"
    subdevice = {
        "name": f"sqeezeMultiAmp Channel #{channel}",
        "identifiers": [f"{node_id}-ch{channel}"],
        "via_device": node_id
    }

    entities += [
        {
            "~": f"{discovery_prefix}/binary_sensor/{node_id}/{node_id}_ch{channel}",
            "unique_id": f"{node_id}_ch{channel}",
            "name": f"sMA Channel #{channel} Container State",
            "object_id": f"{node_id}_ch{channel}",
            "device": subdevice,
            "entity_category": "diagnostic",
            "dev_cla": "running",
            "stat_t": "~/state"
        },
        {
            "~": f"{discovery_prefix}/text/{node_id}/{node_id}_ch{channel}_player_name",
            "unique_id": f"{node_id}_ch{channel}_player_name",
            "name": f"sMA Channel #{channel} Player Name",
            "object_id": f"{node_id}_ch{channel}_player_name",
            "device": subdevice,
            "entity_category": "config",
            "icon": "mdi:rename",
            "dev_cla": "running",
            "cmd_t": "~/set",
            "stat_t": "~/state"
        }
    ]

    for eq_channel in eq_channels:
        eq_channel_num = int(eq_channel[:2])
        entities.append({
            "~": f"{discovery_prefix}/number/{node_id}/{node_id}_ch{channel}_eq{eq_channel_num:02d}_eqsetting",
            "unique_id": f"{node_id}_ch{channel}_eq{eq_channel_num:02d}_eqsetting",
            "name": f"sMA Channel #{channel} EQ {eq_channel} setting",
            "object_id": f"{node_id}_ch{channel}_eq{eq_channel_num:02d}_eqsetting",
            "device": subdevice,
            "entity_category": "config",
            "icon": "mdi:tune",
            "cmd_t": "~/set",
            "stat_t": "~/state",
            "min": 36,
            "max": 95
        })

    for eq_preset in eq_presets.keys():
        entities.append({
            "~": f"{discovery_prefix}/button/{node_id}/{node_id}_ch{channel}_eqpreset_{eq_preset}",
            "unique_id": f"{node_id}_ch{channel}_eqpreset_{eq_preset}",
            "name": f"sMA Channel #{channel} EQ preset {eq_preset}",
            "object_id": f"{node_id}_ch{channel}_eqpreset_{eq_preset}",
            "device": subdevice,
            "entity_category": "config",
            "icon": "mdi:folder-star",
            "cmd_t": f"{discovery_prefix}/button/{node_id}/{node_id}_ch{channel}_eqpreset/set",
            "pl_prs": eq_preset
        })

    entities += [
        {
            "~": f"{discovery_prefix}/number/{node_id}/{node_id}_ch{channel}_volume",
            "unique_id": f"{node_id}_ch{channel}_volume",
            "name": f"sMA Channel #{channel} volume",
            "object_id": f"{node_id}_ch{channel}_volume",
            "device": subdevice,
            "entity_category": "config",
            "icon": "mdi:volume-high",
            "cmd_t": "~/set",
            "stat_t": "~/state",
            "min": 0,
            "max": 100
        },
        {
            "~": f"{discovery_prefix}/text/{node_id}/{node_id}_ch{channel}_hass_switch",
            "unique_id": f"{node_id}_ch{channel}_hass_switch",
            "name": f"sMA Channel #{channel} external switch",
            "object_id": f"{node_id}_ch{channel}_hass_switch",
            "description": "Home Assistant entity id that should be switched on/off based on player state",
            "device": subdevice,
            "entity_category": "config",
            "icon": "mdi:electric-switch",
            "cmd_t": "~/set",
            "stat_t": "~/state"
        }
    ]