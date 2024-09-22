import os
from app_package.generate_subtitles.helper import format_time, header_file
from app_package.helpers.json_action import read_json, write_json

def link_to_reels_action_generate_subtitles(ass_filepath, extracted_words_filepath, logging_object):
    # Read json data extracted_words_filepath
    subtitles_data, dimension = read_json(extracted_words_filepath)
    if not subtitles_data or not dimension:
        print(f"Error@generate_subtitles.link_to_reels_action_insert_subtitles :: Missing either json data or dimension value :: payload: {logging_object}")
        return False
    
    # Get header string
    ass_header = header_file("Social Media Reels Subtitles", dimension)
    
    try:
        # Generate ASS subtitle content
        ass_subtitles = []
        last_end_time = None

        for subtitle in subtitles_data:
            # Convert start and end times to float
            start_time = float(subtitle["start"])
            end_time = float(subtitle["end"])

            # Ensure text is a string
            text = str(subtitle["text"]).replace('\n', '\\N')

            # Adjust start time to prevent overlap
            if last_end_time is not None:
                start_time = max(last_end_time, start_time)

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

            # Add fade-in and fade-out animation
            ass_subtitles.append(f"Dialogue: Marked=0,{start_time_ass},{end_time_ass},Default,,0,0,0,,{animation}{text}\n")

            # Update last_end_time
            last_end_time = end_time
        
        # Combine header and subtitles
        full_content = ass_header + ''.join(ass_subtitles)

        # Save all files
        if not write_json(full_content, ass_filepath):
            print(f"Error@generate_subtitles.link_to_reels_action_insert_subtitles :: Failed to write the output to the ass file: Delete it and retry :: payload: {logging_object, f'ass_filepath: {ass_filepath}'}")
            return False
        
        return True
    except Exception as e:
        print(f"Error@generate_subtitles.link_to_reels_action_insert_subtitles :: An unexpected error occurred while extracting audio filepaths :: error: {e}, payload: {logging_object}")
        return False
