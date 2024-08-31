import ffmpeg
import os
import json
def generate_ass_subtitles(subtitles_data_filepath, output_file):
    """
    Write subtitles data to an ASS file with animation and position adjustment.

    :param subtitles_data: List of subtitle dictionaries.
    :param output_file: Path to the output ASS file.
    """
    # ASS file header
    ass_header = """
    [Script Info]
    Title: Example Subtitle
    Original Script: Assistant
    ScriptType: v4.00
    Collisions: Normal
    PlayDepth: 0

    [V4+ Styles]
    Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaLevel, Encoding
    Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H000000FF,&H00000000,0,0,1,1.00,0.00,2,10,10,1344,0,1

    [Events]
    """
    # Generate ASS subtitle content
    ass_subtitles = ""
    with open(subtitles_data_filepath, 'r') as file:
        subtitles_data = json.load(file)
    for subtitle in subtitles_data:
        try:
            # Convert start and end times to float
            start_time = float(subtitle["start"])
            end_time = float(subtitle["end"])

            # Ensure text is a string
            text = str(subtitle["text"]).replace('\n', '\\N')

            #Calculate the duration for the subtitle
            total_duration = end_time - start_time


            # Define pop_duration and shrink_duration as fractions of total_duration
            pop_duration = total_duration * 0.25  # 25% of total duration
            shrink_duration = total_duration * 0.25  # 25% of total duration
            
            # Convert durations to milliseconds for animation
            pop_duration_ms = pop_duration * 1000
            shrink_duration_ms = shrink_duration * 1000

            # Define the keyframes for animation
            animation = (
                f"{{\\an8\\1c&HFFFFFF&\\fs40\\bord1\\shad0"
                f"\\t(0,{pop_duration_ms},\\fscx120)\\t({pop_duration_ms},{pop_duration_ms+shrink_duration_ms},\\fscx100)}}"
            )

            # Format times for ASS
            start_time_ass = format_time(start_time)
            end_time_ass = format_time(end_time)

            # Add fade-in and fade-out animation
            ass_subtitles += f"Dialogue: Marked=0,{start_time_ass},{end_time_ass},Default,,0,0,0,,{animation}{text}\n"

        except KeyError as e:
            print(f"Missing key in subtitle data: {e}")
        except Exception as e:
            print(f"Error processing subtitle entry: {e}")

    # Output file path

    # Write the ASS file
    try:
        with open(output_file, 'w') as f:
            f.write(ass_header)
            f.write(ass_subtitles)

        print(f"ASS file saved successfully to {output_file}")

    except Exception as e:
        print(f"Error saving ASS file: {e}")

def format_time(seconds):
    """
    Convert time in seconds to ASS time format.

    :param seconds: Time in seconds.
    :return: Time in ASS format (HH:MM:SS.MS).
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{int(hours):01}:{int(minutes):02}:{int(seconds):02}.{milliseconds:03}"

def add_subtitles(video_file, subtitles_file, output_file):
    """
    Add subtitles to the video file.

    :param video_file: Path to the video file.
    :param subtitles_file: Path to the subtitle file.
    :param output_file: Path to the output video file with subtitles.
    """
    ffmpeg.input(video_file).output(output_file, vf=f'subtitles={subtitles_file}').run()

def generate_subtitles(subtitles_data_filepath, filename):
    # Generate subtitles
    generate_ass_subtitles(subtitles_data_filepath, filename)
    print(f'Subtitles saved to {filename}')