FROM python:3.11-slim

RUN mkdir -p /usr/share/fonts/TTF

COPY src src
COPY requirements.txt .
COPY config.toml .
COPY assets/GoMonoNerdFontMono-Regular.ttf\
    /usr/share/fonts/TTF/GoMonoNerdFontMono-Regular.ttf

RUN --mount=type=cache,target=/root/.cache/pip\
    pip install -r requirements.txt

VOLUME ["/data"]

CMD ["python", "src/main.py"] # NOTE: add `--test` flag to run in debug mode
