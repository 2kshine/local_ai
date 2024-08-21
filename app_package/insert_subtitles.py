import ffmpeg
import os

def generate_ass_subtitles(subtitles_data, output_file):
    """
    Generate an ASS subtitle file from the given subtitle data.

    :param subtitles_data: List of dictionaries containing subtitle information.
    :param output_file: Path to the output ASS file.
    """
    # Header for the ASS file
    ass_header = """[Script Info]
Title: Reels AI Subtitles
Original Script: Shining Maharjan
ScriptType: v4.00
Collisions: Normal
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaLevel, Encoding
Style: Default,Arial Bold,28,&H00FFFFFF,&H0000FFFF,&H00FF00FF,&H000000FF,1,0,1,1.0,0.0,2,10,10,10,0,1

[Events]
"""

    # Convert subtitle data to ASS format with animations
    ass_subtitles = ""
    new_start_time = 0
    new_end_time = 0
    for subtitle in subtitles_data:
        start_time = format_time(new_start_time - 3)
        new_end_time = new_start_time + (subtitle["end"] - subtitle["start"])
        end_time = format_time(new_end_time - 3)
        new_start_time = new_end_time
        text = subtitle["text"].replace('\n', '\\N')
        # Add fade-in and fade-out animation
        ass_subtitles += f"Dialogue: Marked=0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
    
    # Write the ASS file
    with open(output_file, 'w') as f:
        f.write(ass_header)
        f.write(ass_subtitles)

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

def generate_subtitles(subtitles_data, filename):
    # Generate subtitles
    generate_ass_subtitles(subtitles_data, filename)
    print(f'Subtitles saved to {filename}')