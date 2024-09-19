import os
import subprocess

from app_package.directory_helper import FINAL_REEL_RENDER, FINAL_VIDEO_DIR, SUBTITLES_PATH_DIR, TRACK_ASSETS

def final_reel_render(filename):
    basename, _ = os.path.splitext(filename)
    output_path = os.path.join(FINAL_REEL_RENDER, f"{basename}.mp4")
    video_path = os.path.join(FINAL_VIDEO_DIR, f"{basename}.mp4")
    subtitles_path = os.path.join(SUBTITLES_PATH_DIR, f"{basename}.ass")
    
    # Check if paths exist
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return
    if not os.path.exists(subtitles_path):
        print(f"Subtitle file not found: {subtitles_path}")
        return

    command = [
        'ffmpeg',
        '-i', video_path,          # Input video file
        '-vf', f'ass={subtitles_path}',  # Input ASS subtitle file
        '-c:v', 'libx264',            # Use libx264 codec for video
        '-c:a', 'copy',               # Copy the audio codec
        '-preset', 'fast',        # Encoding preset
        '-loglevel', 'info',
        '-y',                         # Overwrite output file if it exists
        output_path                   # Output file
    ]

    try:
        subprocess.run(command, check=True)
        print(f'Successfully merged video and subtitles into {output_path}')
    except subprocess.CalledProcessError as e:
        print(f'Error occurred: {e}')
