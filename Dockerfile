FROM alpine:3.17 as builder

ENV LANG C.UTF-8

RUN apk update \
    && apk add --no-cache build-base alsa-lib-dev linux-headers python3 python3-dev py3-pip

RUN mkdir -p /usr/local/src

RUN cd /usr/local/src \
    && wget https://github.com/raedwulf/alsaequal/archive/refs/heads/master.zip -O alsaequal.zip \
    && unzip alsaequal.zip \
    && cd alsaequal-master \
    && make \
    && mkdir -p /usr/lib/alsa-lib \
    && make install

RUN mkdir /wheels

RUN pip install wheel \
    && pip wheel --wheel-dir=/wheels dbus-fast \
    && pip wheel --wheel-dir=/wheels zeroconf \
    && pip wheel --wheel-dir=/wheels https://github.com/aschamberger/LMSTools/archive/development.tar.gz

FROM alpine:3.17

ENV LANG C.UTF-8

RUN apk update \
    && apk add --no-cache tini su-exec python3 py3-pip alsa-utils ladspa docker-cli-compose uhubctl openssh sshpass

RUN apk add caps --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing/

# add group piaudio and pigpio with gid of underlying raspberry os groups
RUN addgroup -g 29 -S piaudio \
    && addgroup -g 997 -S pigpio \
    && adduser -S supervisor \
	&& addgroup supervisor piaudio \
	&& addgroup supervisor pigpio

# create file to be able to map host asound.conf
RUN touch /etc/asound.conf

COPY --from=builder /usr/lib/alsa-lib/libasound_module_pcm_equal.so /usr/lib/alsa-lib/libasound_module_pcm_equal.so
COPY --from=builder /usr/lib/alsa-lib/libasound_module_ctl_equal.so /usr/lib/alsa-lib/libasound_module_ctl_equal.so

COPY --from=builder /wheels /wheels

RUN pip install --no-index --find-links=/wheels dbus-fast \
    && pip install --no-index --find-links=/wheels zeroconf \
    && pip install --no-index --find-links=/wheels LMSTools

RUN pip install \
    asyncio-mqtt \
    python-dotenv

COPY alsa.py /usr/local/bin/alsa.py
COPY backup.py /usr/local/bin/backup.py
COPY compose.py /usr/local/bin/compose.py
#COPY power.py /usr/local/bin/dbus.py
COPY supervisor.py /usr/local/bin/supervisor.py
COPY supervisor.sh /usr/local/bin/supervisor.sh
RUN chmod +x /usr/local/bin/supervisor.sh

ENTRYPOINT [ "/sbin/tini", "--" ]
CMD [ "supervisor.sh" ]
