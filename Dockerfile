FROM alpine:3.20.1 as builder

#ARG ALSAEQUAL_VERSION=master
# use older commit to be compatible with version from raspberry pi OS
ARG ALSAEQUAL_VERSION=0e9c8c3ed426464609114b9402b71b4cc0edabc9

ENV LANG C.UTF-8

RUN apk update \
    && apk add --no-cache build-base alsa-lib-dev linux-headers

RUN mkdir -p /usr/local/src

RUN cd /usr/local/src \
    # && wget https://github.com/raedwulf/alsaequal/archive/0e9c8c3ed426464609114b9402b71b4cc0edabc9.zip -O alsaequal.zip \
    && wget https://github.com/raedwulf/alsaequal/archive/$ALSAEQUAL_VERSION.zip -O alsaequal.zip \
    && unzip alsaequal.zip \
    && cd alsaequal-$ALSAEQUAL_VERSION \
    && make \
    && mkdir -p /usr/lib/alsa-lib \
    && make install

#RUN apk update \
#    && apk add --no-cache python3 python3-dev py3-pip

#RUN mkdir /wheels

#ENV PIP_BREAK_SYSTEM_PACKAGES 1
#RUN pip install wheel \
#    && pip wheel --wheel-dir=/wheels dbus-fast

FROM alpine:3.20.1

ENV LANG C.UTF-8

RUN apk update \
    && apk add --no-cache tini su-exec python3 py3-pip py3-aiohttp py3-rpigpio py3-zeroconf alsa-utils ladspa docker-cli-compose openssh sshpass libusb

RUN apk add caps --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community/

# add group piaudio and docker with gid of underlying raspberry os groups
RUN addgroup -g 29 -S piaudio \
    && addgroup -g 997 -S pigpio \
    && addgroup -g 995 -S docker \
    && adduser -S supervisor \
    && addgroup supervisor piaudio \
    && addgroup supervisor pigpio \
    && addgroup supervisor docker

# create file to be able to map host asound.conf
RUN touch /etc/asound.conf

COPY --from=builder /usr/lib/alsa-lib/libasound_module_pcm_equal.so /usr/lib/alsa-lib/libasound_module_pcm_equal.so
COPY --from=builder /usr/lib/alsa-lib/libasound_module_ctl_equal.so /usr/lib/alsa-lib/libasound_module_ctl_equal.so

#COPY --from=builder /wheels /wheels

ENV PIP_BREAK_SYSTEM_PACKAGES 1
ENV SKIP_CYTHON 1
#RUN pip install --no-index --find-links=/wheels dbus-fast

RUN pip install \
    aiomqtt \
    dbus-fast \
    pysqueezebox \
    python-dotenv \
    pyusb

COPY alsa.py /usr/local/bin/alsa.py
COPY backup.py /usr/local/bin/backup.py
COPY compose.py /usr/local/bin/compose.py
COPY config.py /usr/local/bin/config.py
COPY lms.py /usr/local/bin/lms.py
COPY power.py /usr/local/bin/power.py
COPY supervisor.py /usr/local/bin/supervisor.py
COPY supervisor.sh /usr/local/bin/supervisor.sh
RUN chmod +x /usr/local/bin/supervisor.sh

ENTRYPOINT [ "/sbin/tini", "--" ]
CMD [ "supervisor.sh" ]
