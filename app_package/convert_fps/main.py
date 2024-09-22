import subprocess
import os 

def link_to_reels_action_convert_fps(raw_video_filepath, converted_filepath, FPS, logging_object):
    # Any extension will be converted to avi
    #When youre scaling or adjusting fps always encode the video.
        
    ffmpeg_command = [
        'ffmpeg',
        '-y',                           # Overwrite output file without asking
        '-i', raw_video_filepath,               # Input video file
        '-vf', f'scale=1920:1080,fps={FPS}',           # Set frame rate to FPS
        '-c:v', 'libx264',              # Use H.264 codec
        '-preset', 'veryslow',            # Use slower preset for better quality
        '-crf', '18',                   # Set constant rate factor (lower is better quality)
        '-c:a', 'copy',                # Copy audio stream without re-encoding
        converted_filepath       # Output file path
    ]

    try:
        # Execute the FFmpeg command
        subprocess.run(ffmpeg_command, check=True)
        
        print(f"Success@convert_fps.link_to_reels_action_convert_fps :: Video successfully converted and saved :: payload: {logging_object, f"raw_video_filepath: {raw_video_filepath}", f"converted_filepath: {converted_filepath}"}")
        return True
    except Exception as e:
        print(f"Error@convert_fps.link_to_reels_action_convert_fps :: FFmpeg failed while converting video fps :: error: {e}, payload: {logging_object, f"raw_video_filepath: {raw_video_filepath}", f"converted_filepath: {converted_filepath}"}")
        return False
    
    finally:
        # Remove the original raw file.
        os.remove(raw_video_filepath)