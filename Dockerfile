FROM python:3.9

ENV HOME="/init"

ADD src /init/src
ADD acl /init/acl

COPY aliases.sh /etc/profile.d/

RUN chmod +x /etc/profile.d/aliases.sh \
    && mkdir /init \
    && pip install slack_sdk async-hvac requests kubernetes

CMD tail -f /dev/null