FROM python:3.11-slim

# Install git and cron
RUN apt-get update && apt-get install -y git cron && rm -rf /var/lib/apt/lists/*

# Copy scripts
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

# Copy crontab file and set up cron
COPY crontab.txt /crontab.txt
RUN crontab /crontab.txt

ENV PYTHONUNBUFFERED=1

# Entrypoint: start cron and keep container running
ENTRYPOINT ["/entrypoint.sh"]
