FROM python:3.11-slim

RUN mkdir -p /usr/share/fonts/TTF

COPY src src
COPY requirements.txt .
COPY config.toml .
COPY assets/GoMonoNerdFontMono-Regular.ttf\
    /usr/share/fonts/TTF/GoMonoNerdFontMono-Regular.ttf

RUN --mount=type=cache,target=/root/.cache/pip\
    pip install -r requirements.txt
RUN mkdir -p /logs

VOLUME ["/data"]

# NOTE: add `--test` flag to run in debug mode
CMD ["sh", "-c", "python src/main.py 2>&1 | tee /logs/logs.log"]
