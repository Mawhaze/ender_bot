FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN mkdir -p /tmp/logs

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/src

CMD [ "python", "src/main.py" ]