from pydub import AudioSegment
from pydub.playback import play
import librosa
import numpy as np
from app_package.helpers.directory_helper import AUDIO_DIR, SONGS_DIR, FINAL_VIDEO_DIR
import os
import random
import subprocess

from app_package.unique_assets import (
    asset_tracker,
    asset_keeper
)

def find_one_key_moment(audio_file, duration_sec=30, threshold=0.5):
    # Load the audio file
    y, sr = librosa.load(audio_file, sr=None)
    
    # Compute short-time energy
    hop_length = 512
    energy = np.array([
        np.sum(np.square(y[i:i + hop_length]))
        for i in range(0, len(y), hop_length)
    ])
    
    # Normalize energy
    energy = energy / np.max(energy)
    
    # Find moments with energy above the threshold
    key_moments = []
    for i, e in enumerate(energy):
        if e > threshold:
            start_time = i * hop_length / sr
            end_time = start_time + duration_sec
            if end_time <= len(y) / sr:
                key_moments.append((start_time, end_time))
                # Return the first key moment found
                return (start_time, end_time)
    
    # Return None if no key moment is found
    return None

def process_audio(filename, segment_duration, BASE_FILENAME):   
    try:
        # Pick a random background song 
        asset_tracker_result = asset_tracker('background_music', BASE_FILENAME)
        all_files = [f for f in os.listdir(SONGS_DIR) if f not in asset_tracker_result]
        if not all_files:
            raise FileNotFoundError("No files found in the songs directory.")
        
        random_file = random.choice(all_files)
        asset_keeper('background_music', BASE_FILENAME, random_file)
        print(f'CHOSEN FILE: {random_file}')
        output_path = os.path.join(AUDIO_DIR, filename)
        audio_path = os.path.join(SONGS_DIR, random_file)

        # Load the audio file
        try:
            audio = AudioSegment.from_file(audio_path)
        except Exception as e:
            raise RuntimeError(f"Error loading audio file {audio_path}: {e}")

        # Find the best moment segment
        try:
            key_moment = random.choice([find_one_key_moment(audio_path, segment_duration, 0.5), (0, 0)])
        except Exception as e:
            raise RuntimeError(f"Error finding key moment: {e}")

        start_time_sec, _ = key_moment
        end_time_sec = start_time_sec + segment_duration

        # Convert start and end times from seconds to milliseconds
        start_time_ms = int(start_time_sec * 1000)
        end_time_ms = int(end_time_sec * 1000)

        print(f'start_time_sec: {start_time_sec}')
        # Apply fade-in and fade-out
        fade_in_duration = 2000
        fade_out_duration = 2000  # 2 seconds

        # Crop the audio segment
        try:
            cropped_audio = audio[start_time_ms:end_time_ms]
        except Exception as e:
            raise RuntimeError(f"Error cropping audio segment: {e}")

        # Apply fade-in and fade-out effects
        if start_time_sec > 0:
            faded_audio = cropped_audio.fade_in(fade_in_duration).fade_out(fade_out_duration)
        else:
            faded_audio = cropped_audio.fade_out(fade_out_duration)

        # Export the result
        try:
            faded_audio.export(output_path, format="mp3")
        except Exception as e:
            raise RuntimeError(f"Error exporting audio file to {output_path}: {e}")

        print(f'Saved cropped and faded audio to {output_path}')
        
    except Exception as e:
        print(f"An error occurred: {e}")


def stitch_all_audios(individual_directory_name):
    video_file = os.path.join(FINAL_VIDEO_DIR, f"{individual_directory_name}.mp4")
    temp_file = os.path.join(FINAL_VIDEO_DIR, f"{individual_directory_name}_temp.mp4")
    background_music_file = os.path.join(AUDIO_DIR, f"{individual_directory_name}_background.mp3")
    original_audio_file = os.path.join(AUDIO_DIR, f"{individual_directory_name}.mp3")
    
    filter_complex = (
        f"ffmpeg -i {video_file} -i {background_music_file} -i {original_audio_file} "
        f"-filter_complex \"[0:a]volume=0.3[a1];"
        f"[1:a]volume=0.3[a2];"
        f"[2:a]volume=0.8[a3];"
        f"[a1][a2]amix=inputs=2:duration=longest[a_mix];"
        f"[a_mix][a3]amix=inputs=2:duration=longest[a_final]\" "
        f"-map 0:v:0 -map \"[a_final]\" -c:v copy -c:a aac -b:a 192k {temp_file}"
    )
    try:
        result = subprocess.run(filter_complex, shell=True, check=True, text=True, capture_output=True)
        print("Command output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error occurred:")
        print("Error message:", e.stderr)
    
    # Remove an replace original file
    os.remove(video_file)
    os.rename(temp_file, video_file)