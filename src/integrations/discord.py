"""
Discord integration for sending race updates and results.

This module handles all Discord webhook communications including:
- Race start notifications
- Race completion with video
- Winner announcements
- Status updates
"""

import os
import requests
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime


class DiscordIntegration:
    """Handles Discord webhook communications for race events."""
    
    def __init__(self):
        """Initialize Discord integration with webhook URLs from environment."""
        self.webhook_url = self._get_env_var('WEBHOOK_URL')
        self.winner_report_webhook_url = self._get_env_var('DEV_REPORT_WEBHOOK_URL')
        
    def _get_env_var(self, var_name: str) -> Optional[str]:
        """Get environment variable from .env file or system environment."""
        # Try .env file first
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith(f'{var_name}='):
                        return line.strip().split('=', 1)[1]
        
        # Fall back to system environment
        return os.getenv(var_name)
    
    def send_race_start(self) -> bool:
        """Send race start notification to Discord."""
        if not self.winner_report_webhook_url:
            print("Warning: DEV_REPORT_WEBHOOK_URL not configured, skipping Discord start notification")
            return False
            
        timestamp = datetime.utcnow().isoformat() + 'Z'
        status_obj = {"type": "status", "status": "RUNNING", "timestamp": timestamp}
        payload = {"content": str(status_obj).replace("'", '"')}
        
        try:
            response = requests.post(self.winner_report_webhook_url, json=payload)
            if response.status_code in (200, 204):
                print('Race start notification sent to Discord successfully!')
                return True
            else:
                print(f'Failed to send race start notification. Status: {response.status_code}, Response: {response.text}')
                return False
        except Exception as e:
            print(f'Error sending race start notification: {e}')
            return False
    
    def send_race_complete_with_video(self, video_path: str, results_data: Dict[str, Any]) -> bool:
        """Send race completion status with video to Discord."""
        if not self.winner_report_webhook_url:
            print("Warning: DEV_REPORT_WEBHOOK_URL not configured, skipping Discord completion notification")
            return False
            
        if not os.path.exists(video_path):
            print(f"Warning: Video file not found at {video_path}")
            return False
            
        seed_used = results_data.get('rng_seed', None)
        timestamp = datetime.utcnow().isoformat() + 'Z'
        complete_content = json.dumps({
            "type": "status",
            "status": "COMPLETED",
            "seed": str(seed_used),
            "timestamp": timestamp
        })
        
        try:
            filename = os.path.basename(video_path)
            with open(video_path, 'rb') as f:
                files = {'file1': (filename, f, 'video/mp4')}
                payload_complete = {"content": complete_content}
                response_complete = requests.post(self.winner_report_webhook_url, data=payload_complete, files=files)
            
            if response_complete.status_code in (200, 204):
                print('Race completion status and video sent to Discord successfully!')
                return True
            else:
                print(f'Failed to send completion status and video. Status: {response_complete.status_code}, Response: {response_complete.text}')
                return False
        except Exception as e:
            print(f'Error sending race completion notification: {e}')
            return False
    
    def send_winner_announcement(self, results_data: Dict[str, Any], delay_seconds: Optional[float] = None) -> bool:
        """Send winner announcement to Discord, optionally after a delay."""
        if not self.winner_report_webhook_url:
            print("Warning: DEV_REPORT_WEBHOOK_URL not configured, skipping Discord winner announcement")
            return False
            
        # Calculate delay if not provided
        if delay_seconds is None:
            delay_seconds = self._calculate_video_delay(results_data)
        
        if delay_seconds > 0:
            print(f"Waiting {delay_seconds:.2f} seconds before sending winner announcement...")
            time.sleep(delay_seconds)
        
        winner_id = results_data.get('winning_character_id')
        seed_used = results_data.get('rng_seed', None)
        
        if not winner_id:
            print('No winner character ID found, skipping winner announcement')
            return False

        winner_content = json.dumps({"type": "winner", "winner": winner_id, "seed": str(seed_used)})
        payload_winner = {"content": winner_content}
        
        try:
            response_winner = requests.post(self.winner_report_webhook_url, data=payload_winner)
            if response_winner.status_code in (200, 204):
                print('Winner announcement sent to Discord successfully!')
                return True
            else:
                print(f'Failed to send winner announcement. Status: {response_winner.status_code}, Response: {response_winner.text}')
                return False
        except Exception as e:
            print(f'Error sending winner announcement: {e}')
            return False
    
    def _calculate_video_delay(self, results_data: Dict[str, Any]) -> float:
        """Calculate how long to wait before sending winner announcement based on video length."""
        video_length = results_data.get('simulation_length_seconds', None)
        if not video_length:
            print("Video length unknown, using default 60 second delay...")
            return 60.0
        
        # Calculate the actual video length using exponential compression (1/2 per 60s segment)
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
        return video_wait
    
    def cleanup_videos(self, output_dir: str) -> bool:
        """Clean up MP4 files from the output directory."""
        if not os.path.exists(output_dir):
            print(f"Output directory {output_dir} does not exist")
            return False
            
        mp4_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.mp4')]
        if not mp4_files:
            print("No MP4 files found to clean up")
            return True
            
        print("Cleaning up MP4 files from output directory...")
        try:
            for mp4_file in mp4_files:
                mp4_path = os.path.join(output_dir, mp4_file)
                if os.path.exists(mp4_path):
                    os.remove(mp4_path)
                    print(f"Deleted: {mp4_file}")
            print("MP4 cleanup completed successfully!")
            return True
        except Exception as e:
            print(f"Error during MP4 cleanup: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if Discord integration is properly configured."""
        return self.winner_report_webhook_url is not None
