FROM python:3.9

ENV HOME="/init"

RUN mkdir /init && mkdir /init/logs && chmod 777 /init && chmod 777 /init/logs \
 && pip install kubernetes hvac requests flask aiohttp

ADD src /init/src
ADD acl /init/acl

COPY application.properties /init

EXPOSE 5000

CMD ["python",  "/init/src/run.py"]