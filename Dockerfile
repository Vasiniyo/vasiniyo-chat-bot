FROM python:3.11-slim

RUN mkdir -p /usr/share/fonts/TTF

COPY src src
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
RUN mkdir -p /logs

VOLUME ["/data"]

WORKDIR src

CMD ["sh", "-c", "python3 -m vasiniyo_chat_bot 2>&1 | tee /logs/logs.log"]
