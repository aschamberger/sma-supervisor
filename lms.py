#!/usr/bin/python3

from pysqueezebox.discovery import (
    DISCOVERY_MESSAGE,
    BROADCAST_ADDR,
    _unpack_discovery_response,
)
import socket

DISCOVERY_TIMEOUT = 1

def discover():
    servers = []

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(DISCOVERY_TIMEOUT)

    try:
        print("Sending discovery message.")
        sock.sendto(DISCOVERY_MESSAGE, BROADCAST_ADDR)

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                print(f"Received LMS discovery response from {addr}")
                response = _unpack_discovery_response(data, addr)
                if response:
                    if "host" not in response or "json" not in response:
                        print(f"LMS discovery response {response} does not contain enough information to connect")
                    servers.append(response)
            except socket.timeout:
                print("Finished LMS discovery.")
                break
    finally:
        sock.close()

    return servers

if __name__ == '__main__':
    servers = discover()
    print(servers)