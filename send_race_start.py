import os
import requests

# Get WINNER_REPORT_WEBHOOK_URL from .env or environment
WINNER_REPORT_WEBHOOK_URL = None
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip().startswith('WINNER_REPORT_WEBHOOK_URL='):
                WINNER_REPORT_WEBHOOK_URL = line.strip().split('=', 1)[1]
if not WINNER_REPORT_WEBHOOK_URL:
    WINNER_REPORT_WEBHOOK_URL = os.getenv('WINNER_REPORT_WEBHOOK_URL')
if not WINNER_REPORT_WEBHOOK_URL:
    raise ValueError('WINNER_REPORT_WEBHOOK_URL not found in .env file or environment')

payload = {"content": "RUNNING"}
response = requests.post(WINNER_REPORT_WEBHOOK_URL, json=payload)
if response.status_code in (200, 204):
    print('RUNNING message sent to WINNER_REPORT_WEBHOOK_URL successfully!')
else:
    print(f'Failed to send RUNNING message. Status: {response.status_code}, Response: {response.text}')
