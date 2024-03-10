#!/usr/bin/python3

import aiohttp
import asyncio
import json
import os
import tempfile
from dotenv.main import get_key, set_key

envFile = "/etc/opt/compose/.env"

# created, restarting, running, removing, paused, exited and dead
async def get_container_status():
    program = [ 'docker', 'ps', '--format', '{{.Names}}:{{.State}}' ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        return extract_container_status(stdout.decode())
    else:
        print("error")

def extract_container_status(result):
    lines = result.split("\n")
    status = {}
    for line in lines:
        if len(line) > 0:
            line = line.split(':')
            status[line[0]] = line[1]
    return status

async def up(profile, recreate=False, service=None):
    program = [ 'docker', 'compose', '--env-file', envFile, '--profile', profile, 'up', '--detach' ]
    if recreate:
        program.append('--force-recreate')
    if service:
        program.append(service)
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        print(stdout.decode())
        print(stderr.decode())
    else:
        print("error")

async def docker_platform():
    program = [ 'uname', '-m' ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        platform = stdout.decode().strip()
        if platform == "armv7l":
            return {
                "architecture": "arm",
                "os": "linux",
                "variant": "v7"
            }
        elif platform == "aarch64":
            return {
                "architecture": "arm64",
                "os": "linux"
            }

        return None
    else:
        print("error")
        return None

async def is_local_build(service):
    program = [ 'docker', 'compose', '--env-file', envFile, 'config', '--format', 'json', service ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        result = json.loads(stdout.decode())
        if "build" in result["services"][service]:
            return True

        return False
    else:
        print("error")

async def image_from_compose_service(service):
    program = [ 'docker', 'compose', '--env-file', envFile, 'config', '--images', service ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        return stdout.decode().strip()
    else:
        print("error")

async def image_digest_local(image):
    program = [ 'docker', 'images', '-q', '--no-trunc', image ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        return stdout.decode().strip()
    else:
        print("error")

async def image_registry_auth(session, image):
    registry = "ghcr.io"
    org = "library"
    tag = "latest"
    if ":" in image:
        repo, tag = image.split(":")
    else:
        repo = image
    if "/" in repo:
        parts = repo.split("/")
        if len(parts) == 3:
            registry = parts[0]
            org = parts[1]
            repo = parts[2]
        else:
            org = parts[0]
            repo = parts[1]

    base_url = f"https://{registry}/v2/{org}/{repo}"
    token = None

    url = "https://ghcr.io/token"
    params = {
        "service": "ghcr.io",
        "scope": f"repository:{org}/{repo}:pull",
        "client_id": "shell"
    }
    async with session.get(url, params=params) as response:
        data = await response.json()
        token = data["token"]

    return base_url, tag, token

async def image_digest_remote(session, base_url, token, tag):
    url = f"{base_url}/manifests/{tag}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.docker.distribution.manifest.v2+json,application/vnd.oci.image.index.v1+json"
    }
    async with session.get(url, headers=headers) as response:
        data = await response.json()

        if "errors" in data:
            return None

        platform = await docker_platform()
        for manifest in data['manifests']:
            if manifest["platform"] == platform:
                return manifest["digest"]

    return None

async def get_image_versions(session, base_url, token, local_digest, remote_digest):
    url = f"{base_url}/tags/list"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    versions = []
    async with session.get(url, headers=headers) as response:
        data = await response.json()
        for tag in data["tags"]:
            if tag == "latest" or tag == "main":
                continue
            else:
                versions.append(tag[1:])

        # https://stackoverflow.com/a/2574090
        versions.sort(key=lambda s: [int(u) for u in s.split('.')], reverse=True)

    local_version = None
    remote_version = None
    for version in versions:
        tag = f"v{version}"
        digest = await image_digest_remote(session, base_url, token, tag)
        if digest == local_digest:
            local_version = version
        if digest == remote_digest:
            remote_version = version
        if local_version is not None and remote_version is not None:
            break

    return local_version, remote_version

async def image_pull(name):
    program = [ 'docker', 'pull', name ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        print(stdout.decode())
        print(stderr.decode())
    else:
        print("error")

async def image_prune():
    program = [ 'docker', 'image', 'prune', '-f' ]
    p = await asyncio.create_subprocess_exec(*program, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if p.returncode == 0:
        print(stdout.decode())
        print(stderr.decode())
    else:
        print("error")

async def trigger_watchtower(session, port, token):
    url = f"http://127.0.0.1:{port}/v1/update"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    async with session.get(url, headers=headers) as response:
        print(response.status)
        print(await response.text())
        
    return None

def read_config_value(key):
    value = get_key(envFile, key)
    if len(value) == 0:
        value = None

    return value

def update_config_value(key, value):
    # make sure the tmpfile is created in target dir to prevent mess due to the container
    tempfile.tempdir = os.path.dirname(envFile)
    #success, key, value = set_key(file, key, value, quote, export)
    set_key(envFile, key, value, 'never', False)
    # reset tempdir afterwards
    tempfile.tempdir = None
    # https://stackoverflow.com/a/10541972: NamedTemporaryFile is always created with mode 0600
    os.chmod(envFile, 0o666)

async def main():
    print('compose test')

    print(await docker_platform())

    session = aiohttp.ClientSession()

    services = ["supervisor", "squeezelite_tpl"]
    for service in services:
        is_local = await is_local_build(service)
        if not is_local:
            image = await image_from_compose_service(service)
            local_digest = await image_digest_local(image)
            base_url, tag, token = await image_registry_auth(session, image)
            remote_digest = await image_digest_remote(session, base_url, token, tag)
            print(f"{service}: {image}")
            print(f"Local: {local_digest}")
            print(f"Remote: {remote_digest}")
            if "latest" in image:
                versions = await get_image_versions(session, base_url, token, local_digest, remote_digest)
                print(versions)
        else:
            print("local image")

    image = "ghcr.io/aschamberger/sma-squeezelite"
    base_url, tag, token = await image_registry_auth(session, image)
    remote_digest = await image_digest_remote(session, base_url, token, tag)
    print(remote_digest)
    local_digest = remote_digest

    versions = await get_image_versions(session, base_url, token, local_digest, remote_digest)
    print(versions)

    image = "ghcr.io/aschamberger/sma-squeezelite:main"
    base_url, tag, token = await image_registry_auth(session, image)
    print(await image_digest_remote(session, base_url, token, tag))

    await session.close()

    #print(await get_container_status())
    #await up('on')

if __name__ == '__main__':
    asyncio.run(main())
