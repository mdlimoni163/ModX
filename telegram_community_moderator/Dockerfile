FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot ./bot
COPY .env.example ./.env.example

RUN mkdir -p /app/data

CMD ["python", "-m", "bot.main"]
