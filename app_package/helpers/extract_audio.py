import os
import subprocess

def extract_audio(filepath, extract_audio_filepath, is_encode):
    
    # Define the FFmpeg command
    if is_encode:
        ffmpeg_command = [
            'ffmpeg',
            '-y',                          # Overwrite output file without asking
            '-i', filepath,              # Input video file
            '-ac', '2',                   # Set number of audio channels to 2 (stereo)
            '-ar', '44100',               # Set audio sample rate to 44100 Hz
            '-c:a', 'pcm_s16le',          # Use PCM 16-bit little-endian format for WAV
            extract_audio_filepath                # Output audio file path
        ]
    else:
        ffmpeg_command = [
            'ffmpeg',
            '-y',                         
            '-i', filepath,            
            '-c:a', 'copy',       
            extract_audio_filepath               
        ]
    try:
        # Execute the FFmpeg command
        subprocess.run(ffmpeg_command, check=True)
        
        print(f"Success@helpers.extract_audio :: Extracted audio from video successfully and saved :: payload: {f"extract_audio_filepath:  {extract_audio_filepath}", f"filepath: {filepath}"}")
        return True
    except Exception as e:
        print(f"Error@helpers.extract_audio :: An unexpected error occurred while extracting audio filepaths :: error: {e}, payload: {f"extract_audio_filepath:  {extract_audio_filepath}", f"filepath: {filepath}"}")
        return False