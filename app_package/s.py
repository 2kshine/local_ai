import ffmpeg
import os
import json

from app_package.insert_subtitles.helper import format_time
def generate_ass_subtitles(subtitles_data_filepath, output_file):
    with open(subtitles_data_filepath, 'r') as file:
        data = json.load(file)
        subtitles_data = data['subtitles']
        dimension = data['dimension']
    # ASS file header
    ass_header = f"""
    [Script Info]
    Title: TikTok Reels Subtitles
    Original Script: Assistant
    ScriptType: v4.00
    Collisions: Normal
    PlayDepth: 0
    PlayResX: {dimension[0]}
    PlayResY: {dimension[1]}

    [V4+ Styles]
    Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaLevel, Encoding
    Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H000000FF,&H00000000,0,0,1,1.00,0.00,5,10,10,1344,0,1

    [Events]
    """
    # Generate ASS subtitle content
    ass_subtitles = ""
    last_end_time = None
    for subtitle in subtitles_data:
        try:
            # Convert start and end times to float
            start_time = float(subtitle["start"])
            end_time = float(subtitle["end"])

            # Ensure text is a string
            text = str(subtitle["text"]).replace('\n', '\\N')

            # Calculate the duration for the subtitle
            total_duration = end_time - start_time

            # Define pop_duration and shrink_duration as fractions of total_duration
            pop_duration = total_duration * 0.25  # 15% of total duration
            shrink_duration = total_duration * 0.25  # 15% of total duration
            
            # Convert durations to milliseconds for animation
            pop_duration_ms = pop_duration * 1000
            shrink_duration_ms = shrink_duration * 1000

            # Define the keyframes for animation
            animation = (
                f"{{\\pos({dimension[0] /2}, {dimension[1] - (dimension[1] / 3)})\\1c&HFFFFFF&\\fs35\\bord1\\shad0"
                f"\\t(0,{pop_duration_ms},\\fscx135)\\t({pop_duration_ms},{pop_duration_ms+shrink_duration_ms},\\fscx100)}}"
            )

            # Format times for ASS
            start_time_ass = format_time(start_time)
            end_time_ass = format_time(end_time)

            # Adjust start time to prevent overlap
            if last_end_time is not None:
                start_time = max(last_end_time, start_time)

            # Add fade-in and fade-out animation
            ass_subtitles += f"Dialogue: Marked=0,{start_time_ass},{end_time_ass},Default,,0,0,0,,{animation}{text}\n"

            # Update last_end_time
            last_end_time = end_time

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