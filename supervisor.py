#!/usr/bin/python3

import asyncio
import json
import sys
import time

import aiohttp
import alsa
import asyncio_mqtt as aiomqtt
import backup
import compose
import power
from config import (
    discovery_prefix,
    entities,
    eq_channels,
    eq_presets,
    lms_players,
    node_id,
    num_channels,
    subscriptions,
)
from LMSTools import LMSDiscovery
from pysqueezebox import Player, Server
from zeroconf import ServiceBrowser, Zeroconf

# publish entities for mqtt discovery
async def publish_entities(client):
    for entity in entities:
        topic = f"{entity['~']}/config"
        await client.publish(topic, payload=entity, retain=True)

async def publish_backup_config(client):
    host = compose.read_config_value("BACKUP_SSH_HOST")
    port = compose.read_config_value("BACKUP_SSH_PORT")
    user = compose.read_config_value("BACKUP_SSH_USER")
    payload = f"{user}@{host}:{port}"
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_backup_host/state"
    await client.publish(topic, payload=payload)

    payload = compose.read_config_value("BACKUP_SSH_PASSWORD")
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_backup_password/state"
    await client.publish(topic, payload=payload)

    payload = compose.read_config_value("BACKUP_SSH_FOLDER")
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_backup_folder/state"
    await client.publish(topic, payload=payload)

async def publish_volume(client):
    volumes = await get_all_device_volumes()
    for channel in range(1, num_channels+1):
        topic = f"{discovery_prefix}/number/{node_id}_ch{channel:02d}_volume/state"
        await client.publish(topic, payload=volumes[channel])

async def publish_equalizer_settings(client):
    for channel in range(1, num_channels+1):
        settings = await alsa.get_equalizer(channel)
        for eq_channel in range(0, 10):
            topic = f"{discovery_prefix}/number/{node_id}_ch{channel}_eq{eq_channel[:2]}_eqsetting/state"
            await client.publish(topic, payload=settings[eq_channel])

async def publish_player_names_from_name_files(client):
    path = "/etc/opt/squeezelite"
    for channel in range(1, num_channels+1):
        filename = f"{path}/squeeze{channel}.name"
        with open(filename) as f:
            player_name = f.read()
            topic = f"{discovery_prefix}/text/{node_id}_ch{channel:02d}_player_name/state"
            await client.publish(topic, payload=player_name)

async def poll_lms_and_publish_player_names(client, lms_server):
    sleep_interval = 10 # seconds
    saved = []
    while True:
        try:
            for channel in range(1, num_channels+1):
                # do explicit player name request from LMS to pick up eventual name change from LMS GUI
                # pysqueezebox library caches the name on first connection in player object
                result = await lms_server.async_query("name", "?", player=lms_players[channel])
                if result != False:
                    player_name = result["_value"]
                    if saved[channel]:
                        if saved[channel] != player_name:
                            saved[channel] = player_name
                            topic = f"{discovery_prefix}/text/{node_id}_ch{channel:02d}_player_name/state"
                            await client.publish(topic, payload=player_name)

            await asyncio.sleep(sleep_interval)

        except asyncio.CancelledError as error:
            print(f'Error "{error}". LMS name polling cancelled.')

async def publish_container_states(client):
    sleep_interval = 10 # seconds
    saved = []
    while True:
        try:
            container_status = await compose.get_container_status()

            state = None
            if container_status['supervisor']:
                state = container_status['supervisor']
                if saved['supervisor']:
                    if saved['supervisor'] != state:
                        saved['supervisor'] = state
                        topic = f"{discovery_prefix}/binary_sensor/{node_id}_supervisor/state"
                        await client.publish(topic, payload=state)

            for channel in range(1, num_channels+1):
                state = None
                container = f"squeezelite{channel}"
                if container_status[container]:
                    state = container_status[container]
                if saved[container]:
                    if saved[container] != state:
                        saved[container] = state
                        topic = f"{discovery_prefix}/binary_sensor/{node_id}_ch{channel:02d}/state",
                        await client.publish(topic, payload=state)

            await asyncio.sleep(sleep_interval)

        except asyncio.CancelledError as error:
            print(f'Error "{error}". LMS name polling cancelled.')

async def power_off_lms_players(lms_server):
    for channel in range(1, num_channels+1):
        await lms_server.async_query("power", "0", player=lms_players[channel])

async def do_shutdown(client, lms_server, payload, channel, eq_channel):
    # power off all players to prevent speaker plopp
    power_off_lms_players(lms_server)
    await power.power_off()

async def do_restart(client, lms_server, payload, channel, eq_channel):
    # power off all players to prevent speaker plopp
    power_off_lms_players(lms_server)
    await power.reboot()

async def do_compose_recreate(client, lms_server, payload, channel, eq_channel):
    # power off all players to prevent speaker plopp
    power_off_lms_players(lms_server)
    await compose.up("on", True)
    await publish_container_states(client)

async def do_remote_backup(client, lms_server, payload, channel, eq_channel):
    await backup.create_local_backup()
    await backup.copy_backup_to_remote()
    delete_local_backup()

async def set_lms_host(client, lms_server, payload, channel, eq_channel):
    if (":" not in payload):
        payload = f"{payload}:9000"
    compose.update_config_value("LMS_HOST", payload)
    # restart players
    await compose.up("on", True)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_lms_host/state"
    await client.publish(topic, payload=payload)

async def set_mqtt_host(client, lms_server, payload, channel, eq_channel):
    if (":" not in payload):
        payload = f"{payload}:1883"
    compose.update_config_value("MQTT_HOST", payload)
    # restart players
    await compose.up("on", True)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_mqtt_host/state"
    await client.publish(topic, payload=payload)

async def set_hass_host(client, lms_server, payload, channel, eq_channel):
    if (":" not in payload):
        payload = f"{payload}:8123"
    compose.update_config_value("HASS_HOST", payload)
    # restart players
    await compose.up("on", True)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_hass_host/state"
    await client.publish(topic, payload=payload)

async def set_hass_bearer(client, lms_server, payload, channel, eq_channel):
    compose.update_config_value("HASS_BEARER", payload)
    # restart players
    await compose.up("on", True)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_hass_bearer/state"
    await client.publish(topic, payload=payload)

async def set_backup_host(client, lms_server, payload, channel, eq_channel):
    # extract values from payload
    if (":" not in payload):
        payload = f"{payload}:22"
    user, host = payload.split('@')
    host, port = host.split(':')
    compose.update_config_value("BACKUP_SSH_HOST", host)
    compose.update_config_value("BACKUP_SSH_PORT", port)
    compose.update_config_value("BACKUP_SSH_USER", user)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_backup_host/state"
    await client.publish(topic, payload=payload)

async def set_backup_password(client, lms_server, payload, channel, eq_channel):
    compose.update_config_value("BACKUP_SSH_PASSWORD", payload)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_backup_password/state"
    await client.publish(topic, payload=payload)

async def set_backup_folder(client, lms_server, payload, channel, eq_channel):
    compose.update_config_value("BACKUP_SSH_FOLDER", payload)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_backup_folder/state"
    await client.publish(topic, payload=payload)

async def set_player_name(client, lms_server, payload, channel, eq_channel):
    # update player name via LMS, this pushes to update to squeezelite
    await lms_server.async_query("name", payload, player=lms_players[channel])
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_ch{channel}_player_name/state"
    await client.publish(topic, payload=payload)

async def check_and_enable_eq(channel):
    # OUTPUT_CH1=ch1_eq
    config_name = f"OUTPUT_CH{channel}"
    current_config = compose.read_config_value(config_name)
    if current_config[:-3] != '_eq':
        compose.update_config_value(config_name, f"ch{channel}_eq")
        await compose.up("on", True, f"squeezelite{channel}")

async def set_eqsetting(client, lms_server, payload, channel, eq_channel):
    # enables eq in env file if not enabled and restarts container
    await check_and_enable_eq(channel)
    await alsa.set_equalizer_channel(channel, eq_channel, payload)
    topic = f"{discovery_prefix}/number/{node_id}_ch{channel}_eq{eq_channel[:2]}_eqsetting/state"
    await client.publish(topic, payload=payload)

async def set_eqpreset(client, lms_server, payload, channel, eq_channel):
    # enables eq in env file if not enabled and restarts container
    await check_and_enable_eq(channel)
    settings = await alsa.set_equalizer(channel, eq_presets[payload])
    for eq_channel in range(0, 10):
        topic = f"{discovery_prefix}/number/{node_id}_ch{channel}_eq{eq_channel[:2]}_eqsetting/state"
        await client.publish(topic, payload=settings[eq_channel])

async def set_volume(client, lms_server, payload, channel, eq_channel):
    await alsa.set_channel_volume(channel, payload)
    # always do explicit alsactl store to have it saved for e.g. the backup or a power failure
    await alsa.alsactl_store()
    topic = f"{discovery_prefix}/number/{node_id}_ch{channel:02d}_volume/state"
    await client.publish(topic, payload=payload)

async def set_hass_switch(client, lms_server, payload, channel, eq_channel):
    compose.update_config_value(f"HASS_SWITCH_CH{channel}", payload)
    await compose.up("on", True, f"squeezelite{channel}")
    topic = f"{discovery_prefix}/text/{node_id}_ch{channel:02d}_hass_switch/state"
    await client.publish(topic, payload=payload)

async def main():
    session = aiohttp.ClientSession()

    reconnect_interval = 5 # seconds
    background_tasks = set()
    while True:
        try:
            lms_host, lms_port = compose.read_config_value('LMS_HOST').split(':')
            lms_server = Server(session, lms_host, lms_port)
            mqtt_host, mqtt_port = compose.read_config_value('MQTT_HOST').split(':')
            # manually set to hass dev instance
            mqtt_host = "hass-dev:1883".split(':')
            async with aiomqtt.Client(hostname=mqtt_host, port=mqtt_port) as client:
                await publish_entities(client, lms_server)
                # publish player names from squeezelite name files as eventually the LMS
                # does not have any connected players yet and we don't need to wait for player connect
                await publish_backup_config(client, lms_server)
                await publish_volume(client, lms_server)
                await publish_equalizer_settings(client, lms_server)
                await publish_player_names_from_name_files(client, lms_server)

                # pick up player name changes done via LMS GUI via polling
                task1 = asyncio.create_task(poll_lms_and_publish_player_names(client, lms_server))
                # pick up player name changes done via LMS GUI via polling
                task2 = asyncio.create_task(publish_container_states(client, lms_server))
                # Add task to the set. This creates a strong reference.
                background_tasks.add(task1)
                background_tasks.add(task2)
                # To prevent keeping references to finished tasks forever,
                # make each task remove its own reference from the set after
                # completion:
                task1.add_done_callback(background_tasks.discard)
                task2.add_done_callback(background_tasks.discard)

                async with client.messages() as messages:
                    for subscription in subscriptions:
                        await client.subscribe(subscription)
                    async for message in messages:
                        # handle subscriptions and map to function calls
                        topic_levels = message.topic.split('/')
                        cmd = topic_levels[-1] # 'do' or 'set'
                        object_id = topic_levels[-2]
                        action = object_id[len(node_id):] # remove node_id from beginning
                        channel = None
                        eq_channel = None
                        # extract channel if action on channel
                        if action[0:2] == 'ch' and action[4:5] == '_':
                            channel = int(action[2:4])
                            action = action[5:]
                            # extract eq_channel if action on eq_channel
                            if action[0:2] == 'eq' and action[4:5] == '_':
                                eq_channel = int(action[2:4])
                                action = action[5:]

                        # call desired function
                        function = f"{cmd}_{action}"
                        if (globals()[function]):
                            await globals()[function](client, lms_server, message.payload, channel, eq_channel)
                            if function == "set_lms_host" or function == "set_mqtt_host":
                                task1.cancel()
                                task2.cancel()
                                continue
                        else:
                            print(f'Error: function {function} does not exist.')

        except aiomqtt.MqttError as error:
            print(f'Error "{error}". Reconnecting in {reconnect_interval} seconds.')
            await asyncio.sleep(reconnect_interval)

    await session.close()

def find_mqtt_service(self, zeroconf, service_type, name, state_change):
    info = zeroconf.get_service_info(service_type, name)
    if not (service_type == "_mqtt._tcp.local."):
        return

    if state_change is ServiceStateChange.Added:
        host = str(socket.inet_ntoa(info.address))
        port = info.port
        compose.update_config_value('MQTT_HOST', f"{host}:{port}")
    elif state_change is ServiceStateChange.Removed:
        pass

if __name__ == '__main__':
    print('Starting supervisor')

    if compose.read_config_value('MQTT_HOST') is not None:
        mqtt_host = compose.read_config_value('MQTT_HOST').split(':')
        if len(mqtt_host) == 1:
            mqtt_host.append(1883)
            compose.update_config_value('MQTT_HOST', ':'.join(mqtt_host))
    else:
        zeroconf = Zeroconf()
        browser = ServiceBrowser(zeroconf, "_mqtt._tcp.local.", handlers=[find_mqtt_service])
        time.sleep(5)
        zeroconf.close()
        if compose.read_config_value('MQTT_HOST') is None:
            sys.exit('No mqtt broker could be discovered via zeroconf and no config given manually')

    if compose.read_config_value('LMS_HOST') is not None:
        lms_host = compose.read_config_value('LMS_HOST').split(':')
        if len(lms_host) == 1:
            lms_host.append(9000)
            compose.update_config_value('LMS_HOST', ':'.join(lms_host))
    else:
        servers = LMSDiscovery().all()
        if len(servers) == 0:
            sys.exit('No Logitech Media Server could be discovered and no config given manually')
        else:
            lms_host = [servers[0]['host'], servers[0]['port']]
            compose.update_config_value('LMS_HOST', ':'.join(lms_host))

    pretty = json.dumps(entities, indent=4)
    print(pretty)

    asyncio.run(main())