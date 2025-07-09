#!/bin/bash
set -e


# Set permissions for SSH private key if present
if [ -f /root/.ssh/id_ed25519 ]; then
    chmod 600 /root/.ssh/id_ed25519
fi

# Clone the repository if not already present
if [ ! -d /BaftKingsBortsBook ]; then
    git clone git@github.com:ScottWegley/BaftKingsBortsBook.git /BaftKingsBortsBook
fi

# Set permissions for daily_event.sh if it exists
if [ -f /BaftKingsBortsBook/daily_event.sh ]; then
    chmod +x /BaftKingsBortsBook/daily_event.sh
fi

# Start cron in the background
cron

# Tail the cron log to keep the container running and show output
touch /var/log/cron.log
tail -F /var/log/cron.log
