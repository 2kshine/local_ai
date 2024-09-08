from moviepy.editor import VideoFileClip
import os
from app_package.directory_helper import RAW_VIDEO_DIR, AUDIO_DIR
import subprocess

FPS=30

def splitAV_func (filename):
    file_path = os.path.join(RAW_VIDEO_DIR, filename)
    file_name, _ = os.path.splitext(filename)
    file_path_audio = os.path.join(AUDIO_DIR, file_name + '.mp3')

    # Load the video file
    video = VideoFileClip(file_path)

    # Extract and save audio
    audio = video.audio
    audio.write_audiofile(file_path_audio)

def splitAV_func_for_video_process (cropped_video_path, cropped_video_audio_extract_path):
    # Load the video file
    video = VideoFileClip(cropped_video_path)

    # Extract and save audio
    audio = video.audio
    audio.write_audiofile(cropped_video_audio_extract_path)

def convert_video_fps(filename):
    global FPS
    file_path = os.path.join(RAW_VIDEO_DIR, filename)
    file_name, ext = os.path.splitext(filename)
    formatted_file_path_temp = os.path.join(RAW_VIDEO_DIR, file_name + 'temp' + ext)
    ffmpeg_command = [
        'ffmpeg',
        '-i', file_path,                # Input video file
        '-vf', f'fps={FPS}',           # Set frame rate to FPS
        '-c:v', 'libx264',             # Use libx264 codec for video
        '-preset', 'veryslow',             # Slow preset for better quality (you can use 'veryslow' for even better quality)
        '-crf', '18',                  # Constant Rate Factor (lower is higher quality, 18 is a good balance)
        '-c:a', 'copy',                # Copy audio stream without re-encoding
        formatted_file_path_temp       # Output file path
    ]
    try:
        # Execute the FFmpeg command
        subprocess.run(ffmpeg_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg failed with error @convert_video_fps: {e}")
        return

    # Replace the original file with the new file
    if os.path.isfile(file_path):
        os.remove(file_path)  # Remove the original file
    os.rename(formatted_file_path_temp, file_path) 
    print(f"Video successfully converted to 30 fps and saved as {file_path}")