from moviepy.editor import VideoFileClip
import os
from app_package.helpers.directory_helper import RAW_VIDEO_DIR, AUDIO_DIR
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
