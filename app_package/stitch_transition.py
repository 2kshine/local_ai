import subprocess
import os
import random
from app_package.helpers.directory_helper import SOUND_EFFECTS_DIR, PROCESSED_VIDEO_DIR, TEMPORARY_ACTIONS
from pydub import AudioSegment

from app_package.unique_assets import (
    asset_tracker,
    asset_keeper
)

transition_options = [
    'fade',
    'wipeleft',
    'wiperight',
    'wipeup',
    'wipedown',
    'slideleft',
    'slideright',
    'slideup',
    'slidedown',
    'circlecrop',
    'rectcrop',
    'distance',
    'fadeblack',
    'fadewhite',
    'radial',
    'smoothleft',
    'smoothright',
    'smoothup',
    'smoothdown',
    'circleopen',
    'circleclose',
    'vertopen',
    'vertclose',
    'horzopen',
    'horzclose',
    'dissolve',
    'pixelize',
    'diagtl',
    'diagtr',
    'diagbl',
    'diagbr',
    'hlslice',
    'hrslice',
    'vuslice',
    'vdslice',
    'hblur',
    'fadegrays',
    'wipetl',
    'wipetr',
    'wipebl',
    'wipebr',
    'squeezeh',
    'squeezev',
    'zoomin',
    'fadefast',
    'fadeslow',
    'hlwind',
    'hrwind',
    'vuwind',
    'vdwind',
    'coverleft',
    'coverright',
    'coverup',
    'coverdown',
    'revealleft',
    'revealright',
    'revealup',
    'revealdown'
]
def stitch_transition(previous_index, current_index, previousClip_directory, currentClip_directory, BASE_FILENAME):
    try:

        transitions_directory = os.path.join(PROCESSED_VIDEO_DIR, 'transitions')
        #file to delete in transiitons if found and output path
        files_to_delete_in_transition_dir = None
        output_path = None
        
        # Get all the files in the directory
        for filename in os.listdir(transitions_directory):
            file_name, ext = os.path.splitext(filename)
            
            # Split the file name by '_'
            parts = file_name.split('_')
            numbersArray = parts[-1].split("-")

            if str(previous_index) in numbersArray:

                #Override previous
                file_path_new = os.path.join(transitions_directory, filename)
                previousClip_directory = file_path_new
                files_to_delete_in_transition_dir = file_path_new

                # Create a new output file path and filename
                new_file_name = file_name + '-' + current_index + ext
                output_path = os.path.join(transitions_directory, new_file_name)

        # Default file path for transititon directory.
        if files_to_delete_in_transition_dir is None:
            original_filename, ext = os.path.splitext(os.path.basename(previousClip_directory))
            new_filename_org = original_filename + '-' + current_index + ext
            output_path = os.path.join(transitions_directory, new_filename_org)

        # Select a random transition function
        asset_tracker_result = asset_tracker('transition', BASE_FILENAME)
        filtered_transition = [f for f in transition_options if f not in asset_tracker_result]
        selected_transition = random.choice(filtered_transition)
        asset_keeper('transition', BASE_FILENAME, selected_transition)

        # Apply the selected transition
        if not os.path.exists(output_path):
            apply_transition(previousClip_directory, currentClip_directory, output_path, selected_transition, BASE_FILENAME)
        # selected_transition(previousClip_directory, currentClip_directory, output_path)
        print(f"files_to_delete_in_transition_dir{files_to_delete_in_transition_dir}")

        #Delete the file if exist 
        if files_to_delete_in_transition_dir:
            return files_to_delete_in_transition_dir
        

    except Exception as e:
        print(f"Error in stitching transition: {e}")


def apply_transition(input1, input2, output_path, trans_type, BASE_FILENAME):
    # Define the FFmpeg command
    # Offset should be end time - duration of the transition (in seconds)
    calculatePreviousEnd = get_duration(input1)
    calculateCurrentEnd = get_duration(input2)
    total_duration = calculatePreviousEnd + calculateCurrentEnd - 1.00 #make up for the addition

    fade_duration = 1  # Duration of the transition
    input1_audio_length = calculatePreviousEnd - fade_duration
    offset = max(0, input1_audio_length)  # Ensure offset is not negative

    # Get the duration of the selected sound effect 
    asset_tracker_result = asset_tracker('transition_sound_effects', BASE_FILENAME)
    sound_files = [f for f in os.listdir(SOUND_EFFECTS_DIR) if f.endswith(('.mp3')) and f not in asset_tracker_result]
    selected_sound_filename = random.choice(sound_files)
    selected_sound = os.path.join(SOUND_EFFECTS_DIR, selected_sound_filename)
    asset_keeper('transition_sound_effects', BASE_FILENAME, selected_sound_filename)

    #Extend audio and stitch
    add_silence_and_stitch(selected_sound, offset * 1000, input1, input1_audio_length, total_duration)

    trimmed_sound_path = os.path.join(TEMPORARY_ACTIONS, 'extended_audio.mp3')

    try:
        # Adjust filter_complex to ensure the exact length
        filter_complex = (
            f"[0:v]format=pix_fmts=yuva420p[v0];"
            f"[1:v]format=pix_fmts=yuva420p[v1];"
            f"[v0][v1]xfade=transition={trans_type}:duration={fade_duration}:offset={offset},format=yuv420p[v];"
            f"[2:a]volume=1,atrim=start=0:end={total_duration},asetpts=PTS-STARTPTS[a]"
        )

        ffmpeg_command = [
            'ffmpeg',
            '-i', input1,             # Input video 1
            '-i', input2,             # Input video 2
            '-i', trimmed_sound_path, # Sound effect
            '-filter_complex', filter_complex,
            '-map', '[v]',            # Map final video output
            '-map', '[a]',            # Map final audio output
            '-c:v', 'libx264',
            '-preset', 'veryslow',
            '-t', str(total_duration),  # Ensure the output video is exactly calculateCurrentEnd
            '-y',                     # Overwrite output file if exists
            output_path
        ]
        # Execute the FFmpeg command
        subprocess.run(ffmpeg_command, check=True)
        print(f"Crossfade effect applied successfull")
    except subprocess.CalledProcessError as e:
        print("Error occurred while applying crossfade:", e)
    finally:
        # Clean up temporary sound file
        os.remove(trimmed_sound_path)

def get_duration(file_path):
    """Get the duration of an audio file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=nk=1:nw=1', file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        duration = float(result.stdout.strip())
        return duration
    except subprocess.CalledProcessError as e:
        print(f"Error getting audio duration: {e}")
        return None
      
def add_silence_and_stitch(original_audio_path, silence_duration_ms, input1, input1_duration_minus_fade, current_end_duration):
    extended_audio_path = os.path.join(TEMPORARY_ACTIONS, 'extended_audio.mp3')
    if has_audio_track(input1):
        # Extract audio from input1
        audio1_path = os.path.join(TEMPORARY_ACTIONS, 'audio1.wav')

        extract_audio(input1, audio1_path)
        
        # Load the extracted audio from input1
        audio1 = AudioSegment.from_file(audio1_path)
        audio1_duration = input1_duration_minus_fade - get_duration(audio1_path)
        # Create a silent audio segment of the desired duration
        silence = AudioSegment.silent(duration=audio1_duration*1000)
    else:
        # No audio in input1, so use silence as a placeholder
        audio1 = AudioSegment.silent(duration=0)

        # Create a silent audio segment of the desired duration
        silence = AudioSegment.silent(duration=silence_duration_ms)

    # Load the original audio
    original_audio = AudioSegment.from_file(original_audio_path)

    # Combine audio1 with silence and original_audio
    combined_audio = audio1 + silence + original_audio
    combined_audio_duration = len(combined_audio)

    totalLength_ms_second_input = current_end_duration * 1000

    if combined_audio_duration > totalLength_ms_second_input:
        combined_audio = combined_audio[:totalLength_ms_second_input]
    combined_audio.export(extended_audio_path, format="mp3")
    print(f"combined_audio exported!!!!")

    # Clean up temporary files if needed
    if has_audio_track(input1):
        os.remove(audio1_path)
    
def has_audio_track(file_path):
    """Check if the video file has an audio track."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=codec_type',
             '-of', 'default=nk=1:nw=1', file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        # Check if there is any line with 'audio'
        return 'audio' in result.stdout.strip()
    except FileNotFoundError:
        print("ffprobe is not installed or not found in the system PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error checking audio track: {e}")
        return False
    
def extract_audio(input_video_path, output_audio_path):
    """Extract audio from a video file and save it to output_audio_path."""
    command = [
        'ffmpeg',
        '-i', input_video_path,
        '-q:a', '0',
        '-map', 'a',
        output_audio_path
    ]
    try:
        subprocess.run(command, check=True)
        print(f"Extracted audio to {output_audio_path}.")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e}")