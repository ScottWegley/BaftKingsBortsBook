import imageio
import os
import numpy as np
import pygame
from datetime import datetime

class VideoRecorder:
    def __init__(self, width, height, output_dir="output", fps=60):
        self.frames = []
        self.width = width
        self.height = height
        self.fps = fps
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_path = os.path.join(self.output_dir, f"simulation_{timestamp}.mp4")

    def add_frame(self, surface):
        arr = pygame.surfarray.array3d(surface)
        arr = np.transpose(arr, (1, 0, 2))  # (width, height, 3) -> (height, width, 3)
        self.frames.append(arr)

    def save(self, fixed_dt=None):
        if not self.frames:
            print("No frames to save!")
            return

        # If fixed_dt is not provided, save all frames as normal
        if fixed_dt is None:
            imageio.mimsave(self.output_path, self.frames, fps=self.fps, macro_block_size=None)
            print(f"Video saved to: {self.output_path}")
            return

        # Exponential time-lapse: first 60s normal, next 60s 2x, next 60s 4x, etc.
        processed = []
        frame_time = 0.0
        frame_idx = 0
        chunk_len = 60.0  # seconds per chunk
        while frame_idx < len(self.frames):
            chunk = int(frame_time // chunk_len)
            skip = 2 ** chunk
            if (frame_idx % skip) == 0:
                processed.append(self.frames[frame_idx])
            frame_time += fixed_dt
            frame_idx += 1
        imageio.mimsave(self.output_path, processed, fps=self.fps, macro_block_size=None)
        print(f"Video saved to: {self.output_path} (frames: {len(processed)}/{len(self.frames)})")
