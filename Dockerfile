FROM python:3.11-slim

COPY src src
COPY requirements.txt .
COPY config.toml .
RUN --mount=type=cache,target=/root/.cache/pip\
    pip install -r requirements.txt

VOLUME ["/data"]

CMD ["python", "src/main.py"]
