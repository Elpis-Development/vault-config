FROM python:3.9

ENV HOME="/init"

RUN mkdir /init && mkdir /init/logs && chmod 777 /init && chmod 777 /init/logs \
 && pip install slack_sdk async-hvac requests kubernetes flask

ADD src /init/src
ADD acl /init/acl

CMD ["python",  "/init/src/run.py"]