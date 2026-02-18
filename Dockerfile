FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN apt-get update && apt-get install -y gcc default-libmysqlclient-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ app/
COPY run.py .

EXPOSE 20002

CMD ["python", "run.py"]
