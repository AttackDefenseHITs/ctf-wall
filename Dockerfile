FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg curl ca-certificates && \
    curl -fsSL https://ftp-master.debian.org/keys/archive-key-12.asc \
    | gpg --dearmor -o /etc/apt/trusted.gpg.d/debian-archive.gpg && \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

COPY . .

RUN mkdir -p /app/app/static/uploads && chmod 777 /app/app/static/uploads

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
