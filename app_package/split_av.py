from moviepy.editor import VideoFileClip
import os

def splitAV_func (raw_video_file_path, audio_file_path):
    # Load the video file
    video = VideoFileClip(raw_video_file_path)
    # Extract and save audio
    audio = video.audio
    audio.write_audiofile(audio_file_path)

