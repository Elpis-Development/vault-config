FROM python:3.9

ENV HOME="/init"

RUN mkdir /init && mkdir /init/logs && chmod 777 /init && chmod 777 /init/logs \
 && pip install hvac==0.10.14 requests==2.25.1 flask==2.0.1 aiohttp==3.7.4 waitress==2.0.0 pyhcl==0.4.4 kubernetes==17.17.0

COPY src /init/src
COPY hcl /init/hcl

COPY application.properties /init

EXPOSE 5000

CMD ["python",  "/init/src/run.py"]