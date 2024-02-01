FROM python:3.11.7-slim

RUN apt-get -y update && apt-get -y upgrade && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*

WORKDIR /home/tom/topa-demo

COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN rm requirements.txt

COPY src/ src/

CMD ["python", "src/bot/bot_prod.py", "demo"]
