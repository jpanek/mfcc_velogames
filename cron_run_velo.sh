#!/bin/bash

cd /home/juraj/code/velogames || exit 1

LOG_FILE="/home/juraj/code/velogames/logs/cron_log.log"

echo "=== $(date) Starting Velogames scraper ===" >> "$LOG_FILE"

./pull_db.sh >> "$LOG_FILE" 2>&1 || exit 1

xvfb-run -a /home/juraj/code/velogames/venv/bin/python -u utils/run_velo.py >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then

    echo "=== $(date) Scraper successful, pushing DB ===" >> "$LOG_FILE"

    ./push_db.sh >> "$LOG_FILE" 2>&1

else

    echo "=== $(date) Scraper FAILED, DB will NOT be pushed ===" >> "$LOG_FILE"

    exit 1

fi

echo "" >> "$LOG_FILE"
echo "============================================================" >> "$LOG_FILE"

scp "$LOG_FILE" ubuntu@juraj-vps:~/apps/velogames/logs/cron_log.log