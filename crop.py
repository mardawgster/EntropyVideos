import cv2
import os
import subprocess
from pathlib import Path

def crop_video(input_path: str, output_path: str, crop_width: int = 1504, crop_height: int = 1800, bitrate: int = 3000, x_offset: int = None, y_offset: int = 120, frame_step: int = 3):
    """
    Crops a video to specified dimensions using FFmpeg for efficient compression.
    
    Args:
        input_path: Path to input video file
        output_path: Path to save cropped video
        crop_width: Width of crop (default 1504)
        crop_height: Height of crop (default 1600)
        bitrate: Target bitrate in kbps (default 4000 for good quality/size balance)
        x_offset: Horizontal offset from left edge (None = center). Positive = move crop right
        y_offset: Vertical offset from top edge (None = center). Positive = move crop down
        frame_step: Output every Nth frame (default 1 = all frames, 3 = every 3rd frame)
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Video file not found: {input_path}")
    
    # First, get video dimensions
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {input_path}")
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    # Calculate crop position
    if x_offset is None:
        x_start = (frame_width - crop_width) // 2
    else:
        x_start = x_offset
    
    if y_offset is None:
        y_start = (frame_height - crop_height) // 2
    else:
        y_start = y_offset
    
    # Ensure crop doesn't go out of bounds
    x_start = max(0, min(x_start, frame_width - crop_width))
    y_start = max(0, min(y_start, frame_height - crop_height))
    
    # Build crop filter
    crop_filter = f'crop={crop_width}:{crop_height}:{x_start}:{y_start}'
    
    # Add frame decimation filter if frame_step > 1
    if frame_step > 1:
        crop_filter += f',select=not(mod(n\\,{frame_step})),setpts=N/FRAME_RATE/TB'
    
    # Use FFmpeg for efficient H264 encoding with bitrate control
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-vf', crop_filter,
        '-c:v', 'libx264',
        '-b:v', f'{bitrate}k',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-y',  # Overwrite output file
        output_path
    ]
    
    print(f"Cropping with FFmpeg: {crop_width}x{crop_height}")
    print(f"Crop position: ({x_start}, {y_start})")
    print(f"Bitrate: {bitrate}k")
    if frame_step > 1:
        print(f"Frame decimation: 1 out of every {frame_step} frames")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
    except FileNotFoundError:
        print("FFmpeg not found. Falling back to OpenCV VideoWriter...")
        crop_video_opencv(input_path, output_path, crop_width, crop_height)
        return
    
    # Verify file was created
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"Video cropped and saved to: {output_path}")
        print(f"File size: {file_size / (1024*1024):.2f} MB")
    else:
        print(f"ERROR: Output file was not created at {output_path}")


def crop_video_opencv(input_path: str, output_path: str, crop_width: int = 1504, crop_height: int = 1800):
    """Fallback method using OpenCV"""
    cap = cv2.VideoCapture(input_path)
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {input_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H264 - best compression
    out = cv2.VideoWriter(output_path, fourcc, fps, (crop_width, crop_height))
    
    if not out.isOpened():
        print(f"H264 codec not available, trying H263...")
        fourcc = cv2.VideoWriter_fourcc(*'H263')
        out = cv2.VideoWriter(output_path, fourcc, fps, (crop_width, crop_height))
        
        if not out.isOpened():
            print(f"H263 codec not available, trying MJPG...")
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(output_path, fourcc, fps, (crop_width, crop_height))
    
    if not out.isOpened():
        raise ValueError(f"Could not initialize VideoWriter for: {output_path}")
    
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Center crop
    x_start = (frame_width - crop_width) // 2
    y_start = (frame_height - crop_height) // 2
    x_end = x_start + crop_width
    y_end = y_start + crop_height
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cropped = frame[y_start:y_end, x_start:x_end]
        success = out.write(cropped)
        if not success:
            print(f"WARNING: Failed to write frame {frame_count}")
        frame_count += 1
    
    cap.release()
    out.release()
    
    # Verify file was created
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"Video cropped and saved to: {output_path}")
        print(f"File size: {file_size / (1024*1024):.2f} MB")
    else:
        print(f"ERROR: Output file was not created at {output_path}")

if __name__ == "__main__":
    # Find all .mp4 files in OscilattingTool directory
    video_dir = "/Users/marcusdibattista/EntropyVideos/OscilattingTool/Originals"
    video_files = sorted([f for f in os.listdir(video_dir) if f.endswith('.mp4')])
    
    if not video_files:
        print(f"No .mp4 files found in {video_dir}")
    else:
        print(f"Found {len(video_files)} video(s) to process\n")
        
        for i, video_file in enumerate(video_files, 1):
            input_video = os.path.join(video_dir, video_file)
            output_dir = "/Users/marcusdibattista/EntropyVideos/OscilattingTool/Modified"
            os.makedirs(output_dir, exist_ok=True)
            output_video = os.path.join(
                output_dir,
                os.path.basename(input_video).replace(".mp4", "_mod.mp4"),
            )
            
            print(f"[{i}/{len(video_files)}] Processing: {video_file}")
            try:
                crop_video(input_video, output_video)
                print()
            except Exception as e:
                print(f"ERROR processing {video_file}: {e}\n")
        
        print("All videos processed successfully.")