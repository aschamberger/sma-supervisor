#!/bin/sh

# run supervisor with user supervisor
exec su-exec supervisor python3 /usr/local/bin/supervisor.py