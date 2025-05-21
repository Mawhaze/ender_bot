FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN mkdir -p /tmp/logs
RUN mkdir -p /tmp/transcribe

RUN apt-get update && apt-get install -y \
    ffmpeg
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/src

CMD [ "python", "src/main.py" ]