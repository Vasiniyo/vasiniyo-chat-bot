FROM python:3.11-slim

COPY src src
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "src/main.py"]
