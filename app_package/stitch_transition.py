import subprocess
import os
import random
from app_package.directory_helper import SOUND_EFFECTS_DIR
from pydub import AudioSegment

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
def stitch_transition(previous_index, current_index, previousClip_directory, currentClip_directory, transitions_directory):
    try:
        
        #file to delete in transiitons if found and output path
        files_to_delete_in_transition_dir = None
        output_path = None
        
        # Get all the files in the directory
        for filename in os.listdir(transitions_directory):
            file_name, ext = os.path.splitext(filename)
            
            # Split the file name by '_'
            parts = file_name.split('_')

            if previous_index in parts[2]:

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
        selected_transition = random.choice(transition_options)

        # Apply the selected transition
        apply_transition(previousClip_directory, currentClip_directory, output_path, selected_transition)
        # selected_transition(previousClip_directory, currentClip_directory, output_path)
        print(f"files_to_delete_in_transition_dir{files_to_delete_in_transition_dir}")

        #Delete the file if exist 
        if files_to_delete_in_transition_dir:
            os.remove(files_to_delete_in_transition_dir)

    except Exception as e:
        print(f"Error in stitching transition: {e}")


def apply_transition(input1, input2, output_path, trans_type):
    # Define the FFmpeg command
    # Offset should be end time - duration of the transition (in seconds)
    calculatePreviousEnd = get_duration(input1)
    calculateCurrentEnd = get_duration(input2) + calculatePreviousEnd
    print(f"{calculatePreviousEnd}")
    print(f"{calculateCurrentEnd}")
    offset = f"{(calculatePreviousEnd - .8):.2f}"  # Assuming transition duration is 1 second
    fade_duration = 1  # Duration of the crossfade

    # Get the duration of the selected sound effect
    sound_files = [f for f in os.listdir(SOUND_EFFECTS_DIR) if f.endswith(('.wav', '.mp3'))]
    selected_sound = os.path.join(SOUND_EFFECTS_DIR, random.choice(sound_files))

    add_silence_and_stitch(selected_sound, float(offset) * 1000)

    extended_audio = os.path.join('extended_audio.mp3')
    extended_length = get_duration(extended_audio)

    timmed_sound_path = extended_audio
    if extended_length > calculateCurrentEnd:
        timmed_sound_path = trim_audio(extended_audio, calculateCurrentEnd)
        extended_length = get_duration(timmed_sound_path)
    print(extended_length)

    try:
        # Define filter_complex as a single string
        filter_complex = (
            f"[0:v]trim=start=0:end={calculatePreviousEnd},format=pix_fmts=yuva420p[v0];"
            f"[1:v]trim=start=0:end={calculateCurrentEnd},format=pix_fmts=yuva420p[v1];"
            f"[v0][v1]xfade=transition={trans_type}:duration={fade_duration}:offset={offset},format=yuv420p[v];"
            f"[2:a]volume=0.1,atrim=start=0:end={extended_length},asetpts=PTS-STARTPTS[a]"
        )

        ffmpeg_command = [
            'ffmpeg',
            '-i', input1,             # Input video 1
            '-i', input2,             # Input video 2
            '-i', timmed_sound_path, # Sound effect
            '-filter_complex', filter_complex,
            '-map', '[v]',            # Map video output
            '-map', '[a]',            # Map audio output
            '-c:v', 'libx264',
            '-preset', 'veryslow',
            '-y',                     # Overwrite output file if exists
            output_path
        ]

        # Execute the FFmpeg command
        subprocess.run(ffmpeg_command, check=True)
        print("Crossfade effect applied successfully.")
    except subprocess.CalledProcessError as e:
        print("Error occurred while applying crossfade:", e)
    finally:
        # Clean up temporary sound file
        os.remove('extended_audio.mp3')
        if timmed_sound_path != extended_audio:
            os.remove(timmed_sound_path)

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

def trim_audio(input_file, duration):
    """Trim the audio file to a specific duration and return the path of the trimmed file."""
    # Create a temporary file path for the trimmed audio
    temp_sound_path = 'temp_trimmed_sound.mp3'
    
    # Build the ffmpeg command
    command = [
        'ffmpeg',
        '-i', input_file,         # Input sound effect
        '-t', str(duration),      # Output duration
        '-c', 'copy',             # Copy codec
        temp_sound_path           # Output file
    ]
    
    try:
        # Execute the command
        subprocess.run(command, check=True)
        print(f"Trimmed sound effect created at {temp_sound_path}.")
        return temp_sound_path
    except subprocess.CalledProcessError as e:
        print(f"Error trimming sound effect: {e}")
        return None
    
def add_silence_and_stitch(original_audio_path, silence_duration_ms):
    # Load the original audio
    original_audio = AudioSegment.from_file(original_audio_path)

    # Create a silent audio segment of the desired duration
    silence = AudioSegment.silent(duration=silence_duration_ms)

    # Concatenate the silence and original audio
    combined_audio = silence + original_audio

    # Export the combined audio to the output file
    combined_audio.export('extended_audio.mp3', format="mp3")