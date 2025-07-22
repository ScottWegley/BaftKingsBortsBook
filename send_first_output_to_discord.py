
import os
import requests
import json
import glob
from datetime import datetime
import time
import subprocess


# Get webhook URLs from .env file first, then environment
WEBHOOK_URL = None
WINNER_REPORT_WEBHOOK_URL = None
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip().startswith('WEBHOOK_URL='):
                WEBHOOK_URL = line.strip().split('=', 1)[1]
            if line.strip().startswith('WINNER_REPORT_WEBHOOK_URL='):
                WINNER_REPORT_WEBHOOK_URL = line.strip().split('=', 1)[1]
if not WEBHOOK_URL:
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
if not WINNER_REPORT_WEBHOOK_URL:
    WINNER_REPORT_WEBHOOK_URL = os.getenv('WINNER_REPORT_WEBHOOK_URL')
if not WEBHOOK_URL:
    raise ValueError('WEBHOOK_URL not found in .env file or environment')


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





# Send completed status (with video) before the video wait
if results_data:
    seed_used = results_data.get('rng_seed', None)
    from datetime import datetime
    timestamp = datetime.utcnow().isoformat() + 'Z'
    complete_content = json.dumps({
        "type": "status",
        "status": "COMPLETED",
        "seed": seed_used,
        "timestamp": timestamp
    })
    with open(first_mp4, 'rb') as f:
        files = {'file1': (filename, f, 'video/mp4')}
        payload_complete = {"content": complete_content}
        response_complete = requests.post(WINNER_REPORT_WEBHOOK_URL, data=payload_complete, files=files)
    if response_complete.status_code in (200, 204):
        print('COMPLETE status and video sent to WINNER_REPORT_WEBHOOK_URL successfully!')
    else:
        print(f'Failed to send COMPLETE status and video to WINNER_REPORT_WEBHOOK_URL. Status: {response_complete.status_code}, Response: {response_complete.text}')

# Wait for the length of the video, then send winner message (no video)
video_length = None
if results_data:
    video_length = results_data.get('simulation_length_seconds', None)
if video_length:
    # Calculate the actual video length using an exponential compression (1/2 per 60s segment)
    sim_remaining = video_length
    video_wait = 0.0
    segment_length = 60.0
    factor = 1.0
    while sim_remaining > 0:
        chunk = min(sim_remaining, segment_length)
        video_wait += chunk * factor
        sim_remaining -= chunk
        factor *= 0.5
    # Add a small buffer
    video_wait += 15
    print(f"Waiting {video_wait:.2f} seconds before sending winner message...")
    time.sleep(video_wait)
else:
    print("Video length unknown, waiting 60 seconds as fallback...")
    time.sleep(60)




# After sleep, send winner message (no video) to WINNER_REPORT_WEBHOOK_URL
if results_data:
    winner_id = results_data.get('winning_character_id')
    seed_used = results_data.get('rng_seed', None)
    if winner_id and WINNER_REPORT_WEBHOOK_URL:
        winner_content = json.dumps({"type": "winner", "winner": winner_id, "seed": str(seed_used)})
        payload_winner = {"content": winner_content}
        response_winner = requests.post(WINNER_REPORT_WEBHOOK_URL, data=payload_winner)
        if response_winner.status_code in (200, 204):
            print('Winner message sent to WINNER_REPORT_WEBHOOK_URL successfully!')
        else:
            print(f'Failed to send winner message to WINNER_REPORT_WEBHOOK_URL. Status: {response_winner.status_code}, Response: {response_winner.text}')
    else:
        print('No winner id found or WINNER_REPORT_WEBHOOK_URL not set.')

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
