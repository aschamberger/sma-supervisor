#!/bin/sh

# https://stackoverflow.com/q/59812009
export PYTHONUNBUFFERED=1

# run supervisor with user supervisor
exec su-exec supervisor python3 /usr/local/bin/supervisor.py