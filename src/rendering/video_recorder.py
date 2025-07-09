import imageio
import os
import numpy as np
import pygame
from datetime import datetime

class VideoRecorder:
    def __init__(self, width, height, output_dir="output", fps=60):
        self.width = width
        self.height = height
        self.fps = fps
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_path = os.path.join(self.output_dir, f"simulation_{timestamp}.mp4")
        
        # Initialize streaming writer for memory efficiency
        self.writer = None
        self.frame_count = 0
        self.total_frames_processed = 0  # Track all frames for skip logic

    def add_frame(self, surface, fixed_dt=None):
        """Add a frame to the video - streams directly to disk for memory efficiency with exponential speed-up"""
        self.total_frames_processed += 1
        
        # If fixed_dt is provided, implement exponential time-lapse: first 60s normal, next 60s 2x, next 60s 4x, etc.
        if fixed_dt is not None:
            frame_time = self.total_frames_processed * fixed_dt
            chunk_len = 60.0  # seconds per chunk
            chunk = int(frame_time // chunk_len)
            skip = 2 ** chunk
            
            # Only record every nth frame based on current chunk
            if (self.total_frames_processed % skip) != 0:
                return  # Skip this frame
        
        # Process and write the frame
        arr = pygame.surfarray.array3d(surface)
        arr = np.transpose(arr, (1, 0, 2))  # (width, height, 3) -> (height, width, 3)
        
        # Initialize writer on first frame
        if self.writer is None:
            self.writer = imageio.get_writer(self.output_path, fps=self.fps, macro_block_size=None)
        
        # Write frame directly to disk
        self.writer.append_data(arr)
        self.frame_count += 1

    def save(self, fixed_dt=None):
        """Finalize and close the video file"""
        if self.writer is None:
            print("No frames to save!")
            return
        
        # Close the writer to finalize the video
        self.writer.close()
        
        if fixed_dt is not None:
            print(f"Video saved to: {self.output_path} (frames: {self.frame_count}/{self.total_frames_processed})")
        else:
            print(f"Video saved to: {self.output_path} (frames: {self.frame_count})")
