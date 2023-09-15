#!/usr/bin/python3

import asyncio
import json
import sys
import time

import aiohttp
import aiomqtt
import alsa
import backup
import compose
import lms
import power
import RPi.GPIO as GPIO
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
from pysqueezebox import Server as LmsServer
from zeroconf import ServiceBrowser, Zeroconf

# publish entities for mqtt discovery
async def publish_entities(client):
    for entity in entities:
        topic = f"{entity['~']}/config"
        await client.publish(topic, payload=json.dumps(entity), retain=True)

async def publish_gpio_config(client):
    relay = compose.read_config_value("GPIO_PSU_RELAY")
    delay_on = compose.read_config_value("PSU_POWER_ON_DELAY")
    delay_down = compose.read_config_value("PSU_POWER_DOWN_DELAY")
    payload = f"{relay};{delay_on};{delay_down}"
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_gpio_psu_relay/state"
    await client.publish(topic, payload=payload)

    payload = compose.read_config_value("GPIO_PSU_RELAY_OFF_ON_AMP_SHUTDOWN")
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_gpio_mute/state"
    await client.publish(topic, payload=payload)

    payload = compose.read_config_value("GPIO_USB_POWER")
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_gpio_usb_dac/state"
    await client.publish(topic, payload=payload)

    sps = [""]*num_channels
    for channel in range(1, num_channels+1):
        config = compose.read_config_value(f"GPIO_CH{channel}_SPS")
        if config is not None:
            sps[channel-1] = config
    payload = ";".join(sps)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_gpio_sps/state"
    await client.publish(topic, payload=payload)

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

async def publish_hass_config(client):
    payload = compose.read_config_value("HASS_HOST")
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_hass_host/state"
    await client.publish(topic, payload=payload)

    payload = compose.read_config_value("HASS_BEARER")
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_hass_bearer/state"
    await client.publish(topic, payload=payload)

async def publish_mqtt_config(client):
    host = compose.read_config_value("MQTT_HOST")
    user = compose.read_config_value("MQTT_USER")
    payload = f"{user}@{host}"
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_mqtt_host/state"
    await client.publish(topic, payload=payload)

    payload = compose.read_config_value("MQTT_PASSWORD")
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_mqtt_password/state"
    await client.publish(topic, payload=payload)

async def publish_lms_config(client):
    payload = compose.read_config_value("LMS_HOST")
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_lms_host/state"
    await client.publish(topic, payload=payload)

async def publish_hass_switch(client):
    for channel in range(1, num_channels+1):
        switch = compose.read_config_value(f"HASS_SWITCH_CH{channel}")
        topic = f"{discovery_prefix}/text/{node_id}/{node_id}_ch{channel:02d}_hass_switch/state"
        await client.publish(topic, payload=switch)

async def publish_volume(client):
    volumes = await alsa.get_all_device_volumes()
    for channel in range(1, num_channels+1):
        topic = f"{discovery_prefix}/number/{node_id}/{node_id}_ch{channel:02d}_volume/state"
        await client.publish(topic, payload=volumes[channel-1])

async def publish_equalizer_settings(client):
    for channel in range(1, num_channels+1):
        settings = await alsa.get_equalizer(channel)
        for eq_channel in eq_channels:
            eq_channel_num = int(eq_channel[:2])
            topic = f"{discovery_prefix}/number/{node_id}/{node_id}_ch{channel:02d}_eq{eq_channel_num:02d}_eqsetting/state"
            await client.publish(topic, payload=settings[eq_channel_num])

def get_player_names_from_name_files():
    path = "/etc/opt/squeezelite"
    names = []
    for channel in range(1, num_channels+1):
        filename = f"{path}/squeeze{channel}.name"
        with open(filename) as f:
            names.append(f.read())
    return names

async def publish_player_names_from_name_files(client):
    path = "/etc/opt/squeezelite"
    names = get_player_names_from_name_files()
    for channel in range(1, num_channels+1):
        topic = f"{discovery_prefix}/text/{node_id}/{node_id}_ch{channel:02d}_player_name/state"
        await client.publish(topic, payload=names[channel-1])

async def poll_lms_and_publish_player_names(client, lms_server):
    sleep_interval = 1 # seconds
    names = get_player_names_from_name_files()
    while True:
        try:
            for channel in range(1, num_channels+1):
                # do explicit player name request from LMS to pick up eventual name change from LMS GUI
                # pysqueezebox library caches the name on first connection in player object
                result = await lms_server.async_query("name", "?", player=lms_players[channel-1])
                if result != False:
                    player_name = result["_value"]
                    if names[channel-1] != player_name:
                        names[channel-1] = player_name
                        topic = f"{discovery_prefix}/text/{node_id}/{node_id}_ch{channel:02d}_player_name/state"
                        await client.publish(topic, payload=player_name)

            await asyncio.sleep(sleep_interval)

        except asyncio.CancelledError as error:
            print(f'Error "{error}". LMS name polling cancelled.')

async def publish_container_states(client):
    sleep_interval = 1 # seconds
    supervisor = None
    channels = [None for element in range(num_channels)]
    while True:
        try:
            container_status = await compose.get_container_status()

            state = "OFF"
            if 'supervisor' in container_status:
                if container_status['supervisor'] == 'running':
                    state = "ON"

            if supervisor != state:
                supervisor = state
                topic = f"{discovery_prefix}/binary_sensor/{node_id}/{node_id}_supervisor/state"
                await client.publish(topic, payload=state)

            for channel in range(1, num_channels+1):
                container = f"squeezelite{channel}"
                state = "OFF"
                if container in container_status:
                    if container_status[container] == 'running':
                        state = "ON"

                if channels[channel-1] != state:
                    channels[channel-1] = state
                    topic = f"{discovery_prefix}/binary_sensor/{node_id}/{node_id}_ch{channel:02d}/state"
                    await client.publish(topic, payload=state)

            await asyncio.sleep(sleep_interval)

        except asyncio.CancelledError as error:
            print(f'Error "{error}". Container state polling cancelled.')

async def poll_registry_for_container_updates(client, session):
    sleep_interval = 6*60*60 # seconds
    services = ["supervisor", "squeezelite_tpl"]
    while True:
        try:
            for service in services:
                is_local = await is_local_build(service)
                if not is_local:
                    image = await image_from_compose_service(service)
                    local_digest = await image_digest_local(image)
                    base_url, tag, token = await image_registry_auth(session, image)
                    remote_digest = await image_digest_remote(session, base_url, token, tag)
                    if "latest" in image:
                        installed, latest = await get_image_versions(session, base_url, token, local_digest, remote_digest)
                        state = {
                            "installed_version": installed,
                            "latest_version": latest,
                        }
                    else:
                        state = {
                            "installed_version": local_digest,
                            "latest_version": remote_digest,
                        }

                    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_update_{service}/state"
                    await client.publish(topic, payload=json.dumps(state))

            await asyncio.sleep(sleep_interval)

        except asyncio.CancelledError as error:
            print(f'Error "{error}". Container registry polling cancelled.')

async def usb_dac_availability():
    sleep_interval = 60 # seconds
    usb_id_dacs = [0x0d8c, 0x0102]
    usb_id_hub = [0x1a40, 0x0201]
    if compose.read_config_value("GPIO_USB_POWER") is not None:
        gpio_usb_power = int(compose.read_config_value("GPIO_USB_POWER"))
        GPIO.setup(gpio_usb_power, GPIO.OUT)
        if not GPIO.input(gpio_usb_power):
            GPIO.output(gpio_usb_power, 1)
        while True:
            try:
                dac_devices = power.get_usb_devices(usb_id_dacs)
                if len(list(dac_devices)) < 2:
                    GPIO.output(gpio_usb_power, 0)
                    await asyncio.sleep(5)
                    GPIO.output(gpio_usb_power, 1)
                    power.reset_usb_device(usb_id_hub)

                await asyncio.sleep(sleep_interval)

            except asyncio.CancelledError as error:
                print(f'Error "{error}". USB DAC availability cancelled.')

async def power_off_lms_players(lms_server):
    for channel in range(1, num_channels+1):
        await lms_server.async_query("power", "0", player=lms_players[channel-1])

async def do_shutdown(client, lms_server, payload, channel, eq_channel):
    # power off all players to prevent speaker plopp
    await power_off_lms_players(lms_server)
    await power.power_off()

async def do_restart(client, lms_server, payload, channel, eq_channel):
    # power off all players to prevent speaker plopp
    await power_off_lms_players(lms_server)
    await power.reboot()

async def do_compose_recreate(client, lms_server, payload, channel, eq_channel):
    # power off all players to prevent speaker plopp
    power_off_lms_players(lms_server)
    await compose.up("on", True)

async def do_remote_backup(client, lms_server, payload, channel, eq_channel):
    await backup.create_local_backup()
    await backup.copy_backup_to_remote()
    backup.delete_local_backup()

async def do_update_supervisor(client, lms_server, payload, channel, eq_channel):
    image = await compose.image_from_compose_service("supervisor")
    await compose.image_pull(image)
    # power off all players to prevent speaker plopp
    power_off_lms_players(lms_server)
    await power.reboot()

async def do_update_squeezelite(client, lms_server, payload, channel, eq_channel):
    image = await compose.image_from_compose_service("squeezelite")
    await compose.image_pull(image)
    # power off all players to prevent speaker plopp
    power_off_lms_players(lms_server)
    await compose.up("on", True, "squeezelite")

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
    if "@" in payload:
        user, host = payload.split('@')
    else:
        user = ""
        host = payload
    compose.update_config_value("MQTT_HOST", host)
    compose.update_config_value("MQTT_USER", user)
    # restart players
    # TODO: not required for squeezelite instances, so maybe split into two profiles later
    # await compose.up("on", True)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_mqtt_host/state"
    await client.publish(topic, payload=payload)

async def set_mqtt_password(client, lms_server, payload, channel, eq_channel):
    compose.update_config_value("MQTT_PASSWORD", payload)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_mqtt_password/state"
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
    await lms_server.async_query("name", payload, player=lms_players[channel-1])
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_ch{channel:02d}_player_name/state"
    await client.publish(topic, payload=payload)

async def check_and_enable_eq(channel):
    # OUTPUT_CH1=ch1_eq
    config_name = f"OUTPUT_CH{channel}"
    current_config = compose.read_config_value(config_name)
    if current_config[-3:] != '_eq':
        compose.update_config_value(config_name, f"ch{channel}_eq")
        await compose.up("on", True, f"squeezelite{channel}")

async def set_eqsetting(client, lms_server, payload, channel, eq_channel):
    # enables eq in env file if not enabled and restarts container
    await check_and_enable_eq(channel)
    await alsa.set_equalizer_channel(channel, eq_channel, payload)
    topic = f"{discovery_prefix}/number/{node_id}/{node_id}_ch{channel:02d}_eq{eq_channel:02d}_eqsetting/state"
    await client.publish(topic, payload=payload)

async def set_eqpreset(client, lms_server, payload, channel, eq_channel):
    if payload in eq_presets:
        # enables eq in env file if not enabled and restarts container
        await check_and_enable_eq(channel)
        settings = await alsa.set_equalizer(channel, eq_presets[payload])
        for eq_channel in range(0, 10):
            topic = f"{discovery_prefix}/number/{node_id}/{node_id}_ch{channel:02d}_eq{eq_channel:02d}_eqsetting/state"
            await client.publish(topic, payload=settings[eq_channel])

async def set_volume(client, lms_server, payload, channel, eq_channel):
    await alsa.set_channel_volume(channel, payload)
    # always do explicit alsactl store to have it saved for e.g. the backup or a power failure
    await alsa.alsactl_store()
    topic = f"{discovery_prefix}/number/{node_id}/{node_id}_ch{channel:02d}_volume/state"
    await client.publish(topic, payload=payload)

async def set_hass_switch(client, lms_server, payload, channel, eq_channel):
    compose.update_config_value(f"HASS_SWITCH_CH{channel}", payload)
    await compose.up("on", True, f"squeezelite{channel}")
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_ch{channel:02d}_hass_switch/state"
    await client.publish(topic, payload=payload)

async def set_gpio_psu_relay(client, lms_server, payload, channel, eq_channel):
    psu = payload.split(";")
    if len(psu) > 3:
        psu = psu[:3]
    if len(psu) < 3:
        psu = psu + [""]*(3-len(psu))
    compose.update_config_value("GPIO_PSU_RELAY", psu[0])
    compose.update_config_value("PSU_POWER_ON_DELAY", psu[1])
    compose.update_config_value("PSU_POWER_DOWN_DELAY", psu[2])
    await compose.up("on", True)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_gpio_psu_relay/state"
    await client.publish(topic, payload=payload)

async def set_gpio_mute(client, lms_server, payload, channel, eq_channel):
    compose.update_config_value("GPIO_PSU_RELAY_OFF_ON_AMP_SHUTDOWN", payload)
    mute = payload.split(";")
    if len(mute) > num_channels:
        mute = mute[:num_channels]
    if len(mute) < num_channels:
        mute = mute + [""]*(num_channels-len(mute))
    for channel in range(1, num_channels+1):
        compose.update_config_value(f"GPIO_CH{channel}_MUTE", mute[channel-1])
    await compose.up("on", True)

    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_gpio_mute/state"
    await client.publish(topic, payload=";".join(mute))

async def set_gpio_usb_dac(client, lms_server, payload, channel, eq_channel):
    compose.update_config_value("GPIO_USB_POWER", payload)
    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_gpio_usb_dac/state"
    await client.publish(topic, payload=payload)

async def set_gpio_sps(client, lms_server, payload, channel, eq_channel):
    sps = payload.split(";")
    if len(sps) > num_channels:
        sps = sps[:num_channels]
    if len(sps) < num_channels:
        sps = sps + [""]*(num_channels-len(sps))
    for channel in range(1, num_channels+1):
        compose.update_config_value(f"GPIO_CH{channel}_SPS", sps[channel-1])
    await compose.up("on", True)

    topic = f"{discovery_prefix}/text/{node_id}/{node_id}_gpio_sps/state"
    await client.publish(topic, payload=";".join(sps))

async def main():
    await compose.image_prune()
    session = aiohttp.ClientSession()

    reconnect_interval = 5 # seconds
    background_tasks = set() # Add task to the set. This creates a strong reference.
    while True:
        try:
            lms_host, lms_port = compose.read_config_value('LMS_HOST').split(':')
            lms_server = LmsServer(session, lms_host, int(lms_port))
            mqtt_host, mqtt_port = compose.read_config_value('MQTT_HOST').split(':')
            mqtt_user = compose.read_config_value('MQTT_USER')
            mqtt_password = compose.read_config_value('MQTT_PASSWORD')
            async with aiomqtt.Client(hostname=mqtt_host, port=int(mqtt_port), username=mqtt_user, password=mqtt_password) as client:
                await publish_entities(client)
                await publish_gpio_config(client)
                await publish_backup_config(client)
                await publish_hass_config(client)
                await publish_mqtt_config(client)
                await publish_lms_config(client)
                await publish_hass_switch(client)

                # publish player names from squeezelite name files as eventually the LMS
                # does not have any connected players yet and we don't need to wait for player connect
                await publish_player_names_from_name_files(client)

                # make sure usb dacs are available
                task4 = asyncio.create_task(usb_dac_availability())
                background_tasks.add(task4)
                task4.add_done_callback(background_tasks.discard)

                # dac availability must be run once before to make sure we have proper input
                await asyncio.sleep(20)
                await publish_volume(client)
                await publish_equalizer_settings(client)

                # pick up player name changes done via LMS GUI via polling
                task1 = asyncio.create_task(poll_lms_and_publish_player_names(client, lms_server))
                background_tasks.add(task1)
                task1.add_done_callback(background_tasks.discard)

                # pick up container states via polling
                task2 = asyncio.create_task(publish_container_states(client))
                background_tasks.add(task2)
                task2.add_done_callback(background_tasks.discard)

                # pick up new container versions via polling container registry
                task3 = asyncio.create_task(poll_registry_for_container_updates(client, session))
                background_tasks.add(task3)
                task3.add_done_callback(background_tasks.discard)

                async with client.messages() as messages:
                    for subscription in subscriptions:
                        await client.subscribe(subscription)
                    # subscribe to 'homeassistant/status'
                    await client.subscribe("homeassistant/status")
                    async for message in messages:
                        # republish all data when homeassistant/status online
                        if message.topic.matches("homeassistant/status"):
                            if message.payload.decode() == "online":
                                await publish_gpio_config(client)
                                await publish_backup_config(client)
                                await publish_hass_config(client)
                                await publish_mqtt_config(client)
                                await publish_lms_config(client)
                                await publish_hass_switch(client)
                                await publish_volume(client)
                                await publish_equalizer_settings(client)
                                await publish_player_names_from_name_files(client)
                        else:
                            # handle subscriptions and map to function calls
                            topic_levels = str(message.topic).split('/')
                            cmd = topic_levels[-1] # 'do' or 'set'
                            object_id = topic_levels[-2]
                            action = object_id[len(node_id)+1:] # remove node_id from beginning
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
                                await globals()[function](client, lms_server, message.payload.decode(), channel, eq_channel)
                                if function == "set_lms_host" or function == "set_mqtt_host":
                                    task1.cancel()
                                    task2.cancel()
                                    task3.cancel()
                                    task4.cancel()
                                    continue
                                if function == "do_update_supervisor":
                                    # restart version checking to publish latest version state
                                    coro = task3.get_coro()
                                    task3.cancel()
                                    task3 = asyncio.create_task(coro)
                                    background_tasks.add(task3)
                                    task3.add_done_callback(background_tasks.discard)
                                if function == "set_gpio_usb_dac":
                                    # restart dac checking on gpio change
                                    coro = task4.get_coro()
                                    task4.cancel()
                                    task4 = asyncio.create_task(coro)
                                    background_tasks.add(task4)
                                    task4.add_done_callback(background_tasks.discard)
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

    # set pin numbering mode
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

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
        servers = lms.discover()
        if len(servers) == 0:
            sys.exit('No Logitech Media Server could be discovered and no config given manually')
        else:
            lms_host = [servers[0]['host'], servers[0]['json']]
            compose.update_config_value('LMS_HOST', ':'.join(lms_host))

    #pretty = json.dumps(entities, indent=4)
    #print(pretty)

    asyncio.run(main())