FROM python:3.11.7-slim-bullseye

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*

WORKDIR /home/tom/topa-demo

COPY --chown=tom:tom src ./
COPY --chown=tom:tom requirements.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

USER tom
CMD "python3 src/bot/bot_prod.py demo"