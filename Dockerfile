FROM alpine:3.17

ENV LANG C.UTF-8

RUN apk update \
    && apk add --no-cache tini su-exec python3 py3-pip alsa-utils docker-compose uhubctl openssh sshpass

# add group piaudio and pigpio with gid of underlying raspberry os groups
RUN addgroup -g 29 -S piaudio \
    && addgroup -g 997 -S pigpio \
    && adduser -S supervisor \
	&& addgroup supervisor piaudio \
	&& addgroup supervisor pigpio

# create file to be able to map host asound.conf
RUN touch /etc/asound.conf

# create file to be able to map host asound.state
RUN touch /var/lib/alsa/asound.state
	
RUN pip install pydbus python-dotenv paho-mqtt zeroconf https://github.com/aschamberger/LMSTools/archive/development.tar.gz

#COPY alsa.py /usr/local/bin/alsa.py
#COPY backup.py /usr/local/bin/backup.py
#COPY compose.py /usr/local/bin/compose.py
#COPY dbus.py /usr/local/bin/dbus.py
#COPY usb.py /usr/local/bin/usb.py
#COPY supervisor.py /usr/local/bin/supervisor.py
COPY supervisor.sh /usr/local/bin/supervisor.sh
RUN chmod +x /usr/local/bin/supervisor.sh

ENTRYPOINT [ "/sbin/tini", "--" ]
CMD [ "supervisor.sh" ]
