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
        
        # Memory optimization: use temporary file for frames instead of storing in memory
        self.temp_frames_file = os.path.join(self.output_dir, f"temp_frames_{timestamp}.npy")
        self.frame_count = 0
        self.frame_batch = []
        self.batch_size = 30  # Write frames in batches to reduce memory usage
        
    def add_frame(self, surface):
        # Convert surface to array with minimal memory allocation
        arr = pygame.surfarray.array3d(surface)
        arr = np.transpose(arr, (1, 0, 2))  # (width, height, 3) -> (height, width, 3)
        
        # Add to batch
        self.frame_batch.append(arr)
        self.frame_count += 1
        
        # Write batch to disk when full to reduce memory usage
        if len(self.frame_batch) >= self.batch_size:
            self._write_batch_to_disk()
    
    def _write_batch_to_disk(self):
        """Write current batch of frames to temporary file"""
        if not self.frame_batch:
            return
            
        batch_array = np.stack(self.frame_batch)
        
        if os.path.exists(self.temp_frames_file):
            # Append to existing file
            existing = np.load(self.temp_frames_file, allow_pickle=True)
            combined = np.concatenate([existing, batch_array], axis=0)
            np.save(self.temp_frames_file, combined)
        else:
            # Create new file
            np.save(self.temp_frames_file, batch_array)
        
        # Clear batch to free memory
        self.frame_batch = []

    def save(self, fixed_dt=None):
        # Write any remaining frames in batch
        if self.frame_batch:
            self._write_batch_to_disk()
            
        if self.frame_count == 0:
            print("No frames to save!")
            return

        # Load frames from disk in chunks to process with minimal memory usage
        try:
            all_frames = np.load(self.temp_frames_file, allow_pickle=True)
            
            # If fixed_dt is not provided, save all frames as normal
            if fixed_dt is None:
                # Process frames in smaller chunks to reduce memory usage
                chunk_size = 100
                writer = imageio.get_writer(self.output_path, fps=self.fps, macro_block_size=None)
                
                for i in range(0, len(all_frames), chunk_size):
                    chunk = all_frames[i:i+chunk_size]
                    for frame in chunk:
                        writer.append_data(frame)
                        
                writer.close()
                print(f"Video saved to: {self.output_path}")
            else:
                # Exponential time-lapse: first 60s normal, next 60s 2x, next 60s 4x, etc.
                processed = []
                frame_time = 0.0
                frame_idx = 0
                chunk_len = 60.0  # seconds per chunk
                
                # Process in chunks to reduce memory usage
                while frame_idx < len(all_frames):
                    chunk = int(frame_time // chunk_len)
                    skip = 2 ** chunk
                    if (frame_idx % skip) == 0:
                        processed.append(all_frames[frame_idx])
                    frame_time += fixed_dt
                    frame_idx += 1
                    
                    # Write processed frames in batches
                    if len(processed) >= 100:
                        if not hasattr(self, '_writer_initialized'):
                            self._writer = imageio.get_writer(self.output_path, fps=self.fps, macro_block_size=None)
                            self._writer_initialized = True
                        
                        for frame in processed:
                            self._writer.append_data(frame)
                        processed = []
                
                # Write remaining frames
                if hasattr(self, '_writer_initialized'):
                    for frame in processed:
                        self._writer.append_data(frame)
                    self._writer.close()
                else:
                    imageio.mimsave(self.output_path, processed, fps=self.fps, macro_block_size=None)
                
                print(f"Video saved to: {self.output_path} (total frames processed)")
                
        finally:
            # Clean up temporary file
            if os.path.exists(self.temp_frames_file):
                os.remove(self.temp_frames_file)
