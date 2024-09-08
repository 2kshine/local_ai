import subprocess
import os
import random
from app_package.directory_helper import SOUND_EFFECTS_DIR, PROCESSED_VIDEO_DIR
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
def stitch_transition(previous_index, current_index, previousClip_directory, currentClip_directory):
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

            if str(previous_index) in parts[2]:

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
        if not os.path.exists(output_path):
            apply_transition(previousClip_directory, currentClip_directory, output_path, selected_transition)
        # selected_transition(previousClip_directory, currentClip_directory, output_path)
        print(f"files_to_delete_in_transition_dir{files_to_delete_in_transition_dir}")

        #Delete the file if exist 
        if files_to_delete_in_transition_dir:
            return files_to_delete_in_transition_dir
        

    except Exception as e:
        print(f"Error in stitching transition: {e}")


def apply_transition(input1, input2, output_path, trans_type):
    # Define the FFmpeg command
    # Offset should be end time - duration of the transition (in seconds)
    calculatePreviousEnd = get_duration(input1)
    calculateCurrentEnd = get_duration(input2) + calculatePreviousEnd

    print(f"calculatePreviousEnd{calculatePreviousEnd}")
    print(f"calculateCurrentEnd{calculateCurrentEnd}")

    fade_duration = 1  # Duration of the transition
    offset = max(0, calculatePreviousEnd - fade_duration)  # Ensure offset is not negative

    # Generate black screen video using dimensions from input1
    black_screen_path = 'black_screen.mp4'
    create_black_screen_video(input1, black_screen_path, fade_duration)
    print(f"black_screen_path{get_duration(black_screen_path)}")


    # Get the duration of the selected sound effect 
    sound_files = [f for f in os.listdir(SOUND_EFFECTS_DIR) if f.endswith(('.wav', '.mp3'))]
    selected_sound = os.path.join(SOUND_EFFECTS_DIR, random.choice(sound_files))

    #Extend audio and stitch
    add_silence_and_stitch(selected_sound, offset * 1000, input1, calculateCurrentEnd - fade_duration, fade_duration)

    trimmed_sound_path = os.path.join('extended_audio.mp3')

    try:
        # Adjust filter_complex to ensure the exact length
        filter_complex = (
            f"[0:v]trim=start=0:end={calculatePreviousEnd},format=pix_fmts=yuva420p[v0];"
            f"[1:v]trim=start=0:end={calculateCurrentEnd},format=pix_fmts=yuva420p[v1];"
            f"[2:v]trim=start=0:end={fade_duration},format=pix_fmts=yuva420p[v2];"
            f"[v0][v1]xfade=transition={trans_type}:duration={fade_duration}:offset={offset},format=yuv420p[v];"
            f"[v][v2]concat=n=2:v=1:a=0[vout];"
            f"[3:a]volume=1,atrim=start=0:end={calculateCurrentEnd},asetpts=PTS-STARTPTS[a];"
            f"[vout]trim=end={calculateCurrentEnd},setpts=PTS-STARTPTS[vout];"
            f"[a]atrim=end={calculateCurrentEnd},asetpts=PTS-STARTPTS[aout]"
        )

        # FFmpeg command setup
        ffmpeg_command = [
            'ffmpeg',
            '-i', input1,             # Input video 1
            '-i', input2,             # Input video 2
            '-i', black_screen_path,  # Black screen video
            '-i', trimmed_sound_path, # Sound effect
            '-filter_complex', filter_complex,
            '-map', '[vout]',         # Map trimmed video output
            '-map', '[aout]',         # Map trimmed audio output
            '-c:v', 'libx264',
            '-preset', 'veryslow',
            '-t', str(calculateCurrentEnd),  # Ensure the output video is exactly calculateCurrentEnd
            '-y',                     # Overwrite output file if exists
            output_path
        ]
        # Execute the FFmpeg command
        subprocess.run(ffmpeg_command, check=True)
        print(f"Crossfade effect applied successfull with final length of {get_duration(output_path)}")
    except subprocess.CalledProcessError as e:
        print("Error occurred while applying crossfade:", e)
    finally:
        # Clean up temporary sound file
        os.remove('extended_audio.mp3')
        os.remove('black_screen.mp4')

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
    
def add_silence_and_stitch(original_audio_path, silence_duration_ms, input1, totalLength, fade_duration):
    if has_audio_track(input1):
        # Extract audio from input1
        audio1_path = 'audio1.wav'
        extract_audio(input1, audio1_path)
        
        # Load the extracted audio from input1
        audio1 = AudioSegment.from_file(audio1_path)

        # Create a silent audio segment of the desired duration
        silence = AudioSegment.silent(duration=0)
    else:
        # No audio in input1, so use silence as a placeholder
        audio1 = AudioSegment.silent(duration=0)

        # Create a silent audio segment of the desired duration
        silence = AudioSegment.silent(duration=silence_duration_ms)

    # Load the original audio
    original_audio = AudioSegment.from_file(original_audio_path)



    print(f"audio1: {len(audio1)}")
    print(f"audio1: {len(silence)}")
    print(f"audio1: {len(original_audio)}")
    # Combine audio1 with silence and original_audio
    combined_audio = audio1 + silence + original_audio

    extended_length = len(combined_audio)
    print(f"extended_length: {extended_length}")

    # Convert totalLength from seconds to milliseconds
    totalLength_ms = totalLength * 1000

    if extended_length > totalLength_ms:
        # If combined audio exceeds total length, trim it
        trimmed_audio = combined_audio[:totalLength_ms]
        trimmed_audio.export('extended_audio.mp3', format="mp3")
        print(f"Audio trimmed to match total length of {totalLength} seconds.")
    else:
        # If combined audio is shorter, extend with silence
        additional_silence_duration = totalLength_ms - extended_length
        additional_silence = AudioSegment.silent(duration=additional_silence_duration)
        final_audio = combined_audio + additional_silence
        final_audio.export('extended_audio.mp3', format="mp3")
        print(f"Audio extended with silence to match total length of {totalLength} seconds.")

    # Clean up temporary files if needed
    if has_audio_track(input1):
        os.remove(audio1_path)

def create_black_screen_video(input_video_path, output_path, duration):
    """Create a black screen video of a specific duration with the same dimensions as the input video."""
    width, height = get_video_dimensions(input_video_path)
    if width is None or height is None:
        raise ValueError("Failed to get dimensions of the input video.")
    
    command = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'color=c=black:s={width}x{height}:d={duration}',
        '-t', str(duration),
        '-vf', 'fps=30',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        output_path
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Black screen video created at {output_path}.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating black screen video: {e}")
    
def get_video_dimensions(file_path):
    """Get the dimensions of a video file (width x height)."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
             '-of', 'default=nk=1:nw=1', file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        dimensions = result.stdout.strip().split('\n')
        width = int(dimensions[0])
        height = int(dimensions[1])
        return width, height
    except subprocess.CalledProcessError as e:
        print(f"Error getting video dimensions: {e}")
        return None, None
    
def has_audio_track(file_path):
    """Check if the video file has an audio track."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=codec_type',
             '-of', 'default=nk=1:nw=1', file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        return result.stdout.strip() == 'audio'
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