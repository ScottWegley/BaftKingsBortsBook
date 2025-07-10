
import os
import requests
import json
import glob
from datetime import datetime
import time
import subprocess

# Get webhook URL from environment, fallback to .env file if not found
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
if not WEBHOOK_URL:
    # Try to load from .env file in parent directory
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip().startswith('WEBHOOK_URL='):
                    WEBHOOK_URL = line.strip().split('=', 1)[1]
                    break
    if not WEBHOOK_URL:
        raise ValueError('WEBHOOK_URL not found in environment or .env file')

output_dir = os.path.join(os.path.dirname(__file__), 'output')
mp4_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.mp4')]
if not mp4_files:
    raise FileNotFoundError('No MP4 files found in output directory')

mp4_files.sort()
first_mp4 = os.path.join(output_dir, mp4_files[0])
filename = os.path.basename(first_mp4)

# Find the most recent results JSON in results/canon
results_dir = os.path.join(os.path.dirname(__file__), 'results', 'canon')
json_files = [f for f in os.listdir(results_dir) if f.lower().endswith('.json')]
json_path = None
if json_files:
    json_files.sort(key=lambda f: os.path.getmtime(os.path.join(results_dir, f)), reverse=True)
    json_path = os.path.join(results_dir, json_files[0])

results_data = None
if json_path:
    with open(json_path, 'r') as jf:
        results_data = json.load(jf)

# 1. Send the event embed
if results_data:
    # Use only the date part, format as 'Month Day, Year'
    ts = results_data.get('timestamp', None)
    if ts:
        try:
            dt = datetime.fromisoformat(ts)
            event_date = dt.strftime('%B %d, %Y')
        except Exception:
            event_date = 'Unknown'
    else:
        event_date = 'Unknown'
else:
    event_date = 'Unknown'

embed1 = {
    "title": f"Event for {event_date}",
}
payload1 = {"embeds": [embed1]}

response1 = requests.post(WEBHOOK_URL, json=payload1)
if response1.status_code in (200, 204):
    print('Event embed sent successfully!')
else:
    print(f'Failed to send event embed. Status: {response1.status_code}, Response: {response1.text}')

# 2. Send the video by itself (no embed)
with open(first_mp4, 'rb') as f:
    files = {
        'file1': (filename, f, 'video/mp4')
    }
    response2 = requests.post(WEBHOOK_URL, files=files)

if response2.status_code in (200, 204):
    print('Video sent successfully!')
else:
    print(f'Failed to send video. Status: {response2.status_code}, Response: {response2.text}')

# 3. Wait for the length of the video, then send winner embed
video_length = None
if results_data:
    video_length = results_data.get('simulation_length_seconds', None)
if video_length:
    video_length += 5.5
    print(f"Waiting {video_length:.2f} seconds before sending winner embed...")
    time.sleep(video_length)
else:
    print("Video length unknown, waiting 10 seconds as fallback...")
    time.sleep(10)

winner_name = None
if results_data:
    winner_name = results_data.get('winning_character_name')

if winner_name:
    winner_embed = {
        "title": "Winner",
        "description": f"{winner_name}"
    }
    payload_winner = {"embeds": [winner_embed]}
    response3 = requests.post(WEBHOOK_URL, json=payload_winner)
    if response3.status_code in (200, 204):
        print('Winner embed sent successfully!')
    else:
        print(f'Failed to send winner embed. Status: {response3.status_code}, Response: {response3.text}')
else:
    print("No winner name found in results JSON.")

# 4. Clean up: delete MP4 files from output directory
print("Cleaning up MP4 files from output directory...")
try:
    for mp4_file in mp4_files:
        mp4_path = os.path.join(output_dir, mp4_file)
        if os.path.exists(mp4_path):
            os.remove(mp4_path)
            print(f"Deleted: {mp4_file}")
    print("MP4 cleanup completed successfully!")
except Exception as e:
    print(f"Error during MP4 cleanup: {e}")