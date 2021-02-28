FROM python:3.9

ENV HOME="/init"

RUN mkdir /init && mkdir /init/logs && chmod 777 /init && chmod 777 /init/logs \
 && pip install hvac requests flask aiohttp waitress pyhcl kubernetes

ADD src /init/src
ADD hcl /init/hcl

COPY application.properties /init

EXPOSE 5000

CMD ["python",  "/init/src/run.py"]