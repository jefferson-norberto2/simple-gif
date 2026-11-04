import sys
from simplegif.utils.config import ConversionOptions, VideoMetadata
from simplegif.utils.writer import GifWriter
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

for total_frames in [300, 1000, 2000, 3000, 5000]:
    meta = VideoMetadata(width=1280, height=720, fps=30.0, total_frames=total_frames)
    opts_full = ConversionOptions(scale=0.6, frame_skip=5, less_colors=True)
    size_full = GifWriter.estimate_gif_size(meta, opts_full, sample_frame=dummy_frame)
    
    # Selected range of 1500 frames (50.0 seconds at 30 fps)
    opts_half = ConversionOptions(scale=0.6, frame_skip=5, less_colors=True, start_time=0.0, end_time=50.0)
    size_half = GifWriter.estimate_gif_size(meta, opts_half, sample_frame=dummy_frame)

    # Selected range of 2500 frames (83.33 seconds at 30 fps)
    opts_2500 = ConversionOptions(scale=0.6, frame_skip=5, less_colors=True, start_time=0.0, end_time=83.33)
    size_2500 = GifWriter.estimate_gif_size(meta, opts_2500, sample_frame=dummy_frame)
    
    print(f"Total {total_frames}: Full={size_full}, Half(1500f)={size_half}, 2500f={size_2500}")
