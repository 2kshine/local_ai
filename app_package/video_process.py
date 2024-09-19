import os
import numpy as np
from PIL import Image
from moviepy.editor import VideoFileClip, ImageSequenceClip
import json
import subprocess
from app_package.directory_helper import RAW_VIDEO_DIR, CROPPED_VIDEO_DIR, PROCESSED_VIDEO_DIR, FRAMES_FOLDER_DIR, AUDIO_DIR, IMAGE_GENERATION_DIR, WORDS_EXTRACTION_DIR, FINAL_VIDEO_DIR, TEMPORARY_ACTIONS, TRACK_ASSETS
import re
import random

from app_package.intent_identifier import (
    zero_shot_indentify
)

from app_package.image_generation import (
    animate_image
)

from app_package.split_av import (
    splitAV_func_for_video_process
)

from app_package.video_process_helpers import (
    detect_people,
    get_focus_box,
    resize_for_tiktok,
    crop_frame,
    zoom_in_from_sides_except_top,
    ensure_even_dimensions,
    crop_video,
    add_silence
)

from app_package.transcriber import (
    extract_words
)
from app_package.stitch_transition import (
    stitch_transition,
    has_audio_track,
    get_duration,
)
from app_package.background_audio_process import (
    process_audio,
    stitch_all_audios
)

from app_package.unique_assets import (
    asset_tracker,
    asset_keeper
)

GLOBAL_FOCUS_BOX = None
REEL_HEIGHT = None
REEL_WIDTH = None
ACTION_STATUS = None
DIMENSION=(588, 1046)
BASE_FILENAME = None
def extract_and_process_frames(video_path, frames_dir, action):
    global DIMENSION, GLOBAL_FOCUS_BOX
    try:
        """Extract and process frames: detect people, apply random zoom effects, resize for TikTok, and save the frame."""
        clip = VideoFileClip(video_path)
        fps = 30
        duration = clip.duration
        frame_count = int(duration * fps)
        
        for t in range(frame_count):
            frame = clip.get_frame(t / fps)
            frame = np.array(frame)
            people_boxes = detect_people(frame)

            frame_path = os.path.join(frames_dir, f'frame_{t:04d}.png')
            final_verdict_image_ensure = None
            if people_boxes:
                if GLOBAL_FOCUS_BOX is None:
                    # Save initial focus box based on the first frame with detected people
                    focus_box = get_focus_box(people_boxes, frame.shape)
                    cropped_frame = crop_frame(frame, focus_box)
                    image = Image.fromarray(cropped_frame)
                    GLOBAL_FOCUS_BOX = focus_box
                else:
                    focus_box = GLOBAL_FOCUS_BOX
                cropped_frame = crop_frame(frame, focus_box)
                image = Image.fromarray(cropped_frame)


                if(action == "ZOOM"):
                    tiktok_ready_image = resize_for_tiktok(image)
                    zoomed_image = zoom_in_from_sides_except_top(tiktok_ready_image, 1.2)
                    final_verdict_image_ensure = ensure_even_dimensions(zoomed_image) #make sure its divisible int

                else:
                    tiktok_ready_image = resize_for_tiktok(image)
                    final_verdict_image_ensure = ensure_even_dimensions(tiktok_ready_image) #make sure its divisible int

                # Resize for TikTok aspect ratio
                
                # Save processed frame
            else: #Return so that we can put in image instead of people less reel
                # Save original frame if no people are detected
                image = Image.fromarray(frame)
                tiktok_ready_image = resize_for_tiktok(image)
                final_verdict_image_ensure = ensure_even_dimensions(tiktok_ready_image)
            
            if not DIMENSION:
                DIMENSION = final_verdict_image_ensure.size
            else:
                final_verdict_image_ensure = final_verdict_image_ensure.resize(DIMENSION, Image.LANCZOS)
         
            final_verdict_image_ensure.save(frame_path, format='PNG', quality=100)

    except Exception as e:
        print(f"Error found while cropping video from extract_and_process_frames for video_path {video_path}: {e}")
        raise e

def create_video_from_frames(output_video_path, frames_dir):
    try:
        # List and sort frame files
        frame_files = sorted(os.listdir(frames_dir))
        frames = [os.path.join(frames_dir, file) for file in frame_files]
        
        if frames:
            # Create a video clip from the frames
            clip = ImageSequenceClip(frames, fps=30)  # Adjust fps as needed
            
            # Write the video file with HD quality settings
            clip.write_videofile(
                output_video_path, 
                codec='libx264',
                preset='veryslow',  # Use 'veryslow' for the best quality
            )
        else:
            print("No frames available to create the video.")
    except Exception as e:
        print(f"Error found while cropping video from create_video_from_frames for output_video_path {output_video_path}: {e}")
        raise e

def stitch_transition_helper(action_json, processed_path, individual_directory_name):
    global ACTION_STATUS, BASE_FILENAME
    files_to_delete = []
    if not processed_path:
        raise ValueError("No video files found in the directory.")
    print(f"action_json: {action_json}")
    #action_json first index is action second is end time
    try:
        for index, action in enumerate(action_json):
            # if previous index is image or if next index is image, 
            previous_index = None
            current_index = None
            if ACTION_STATUS == 'IMAGE': 
                previous_index = index - 1
            if action == 'IMAGE':
                current_index = index
            if (previous_index is not None or current_index is not None):
                previousClip = individual_directory_name +'_' + str(index - 1) + '.mp4'
                currentClip = individual_directory_name +'_' + str(index) + '.mp4'
                previousClip_directory = os.path.join(processed_path, previousClip)
                currentClip_directory = os.path.join(processed_path, currentClip)
                file_to_delete = stitch_transition(str(index - 1), str(index), previousClip_directory, currentClip_directory, BASE_FILENAME)
                if(file_to_delete):
                    files_to_delete.append(file_to_delete)
            ACTION_STATUS = action
    except Exception as e:
        print(f"Error stitching transaction helpers {processed_path}: {e}")
        raise e

    #Delete previous files.
    for file_path_to_delete in files_to_delete:
        os.remove(file_path_to_delete)

# Main processing function
def video_process(filename, reels_script_path):
    global BASE_FILENAME, DIMENSION
    input_video = os.path.join(RAW_VIDEO_DIR, filename)

    # Load the json script 
    # Open the JSON file for reading
    with open(reels_script_path, 'r') as file:
        # Load JSON data from the file
        reels_script = json.load(file)
    reels_video_script = reels_script['payload']
    reels_result_script = reels_script

    basename, ext = os.path.splitext(filename)
    BASE_FILENAME = basename

    individual_directory_name = basename + '_' + reels_result_script['id'] #directory name for processed video
    filename_unique = individual_directory_name + ext # Unique filename
    filename_unique_segments = individual_directory_name + '_cropped' + ext
    extract_audio_filename = individual_directory_name + '.mp3'
    extract_words_filename = individual_directory_name + '.json'

    # Crop the raw video according to the start time and end time seconds 
    cropped_video_path = os.path.join(CROPPED_VIDEO_DIR, filename_unique)
    cropped_video_path_segments = os.path.join(CROPPED_VIDEO_DIR, filename_unique_segments)
    processed_path = os.path.join(PROCESSED_VIDEO_DIR, individual_directory_name)
    cropped_video_audio_extract_path = os.path.join(AUDIO_DIR, extract_audio_filename)
    extract_words_filepath = os.path.join(WORDS_EXTRACTION_DIR, extract_words_filename)

    # If no directory in processed path for each reels create one 
    if not os.path.exists(processed_path):
        os.makedirs(processed_path)

    # # Crop the video to the specified time range if the file doesnt already exist
    # It crops the long video into the start and end duration of the entire reel.
    # try:
    #     if not (os.path.isfile(cropped_video_path)):
    #         start_time_sec = reels_result_script['results']['period']['startTime']
    #         end_time_sec = reels_result_script['results']['period']['endTime']
    #         crop_video(input_video, cropped_video_path, start_time_sec, end_time_sec)
    # except Exception as e:
    #     print(f"Error found while cropping {filename}: {e}")
    #     raise e
    
    # # Split Audio and video of a raw video if the file doesnt already exist
    # try:
    #     if not (os.path.isfile(cropped_video_audio_extract_path)):
    #         extractedAudioFilePath = splitAV_func_for_video_process(cropped_video_path, cropped_video_audio_extract_path)
    # except Exception as e:
    #     print(f"Error found while splitting cropped video to audio {filename}: {e}")
    #     raise e

    # Always set the first segment and last segment to be a Normal Action
    reels_video_script[0]['action'] = "NORMAL"
    reels_video_script[1]['action'] = "NORMAL"
    reels_video_script[-1]['action'] = "NORMAL"
    
    # # #Loop through each segment, check the action, ignore the first two segment and extract frames and process them 
    # # If current action is image, or next action is image, add/ extend 1 second to the end of the video 
    # for index, restSeg in enumerate(reels_video_script):
    #     isNextIndexImage = None
    #     if (index + 1) < len(reels_video_script) and reels_video_script[(index + 1)]['action'] == "IMAGE":
    #         isNextIndexImage = True
    #     video_process_helper(individual_directory_name,index,processed_path, restSeg, cropped_video_path, cropped_video_path_segments, filename, isNextIndexImage)

    # Remove all cropped files 
    # for file in os.listdir(CROPPED_VIDEO_DIR):
    #     os.remove(os.path.join(CROPPED_VIDEO_DIR, file))

    # Figure out the transition times for all the video segments
    # try:
    #     # Creating the action_json
    #     action_json = [
    #         entry.get('action')
    #         for entry in reels_video_script
    #     ]        
    #     stitch_transition_helper(action_json, processed_path, individual_directory_name)
    # except Exception as e:
    #     print(f"Error found while stitching transitions {filename}: {e}")
    #     raise e

    # #Stitch all the clips and figure out if there are any transitions
    # stitch_video_output(individual_directory_name, processed_path)

    # # #Configure background music based on total video length 
    # process_audio(f'{individual_directory_name}_background.mp3', reels_video_script[-1]['end'], BASE_FILENAME)

    # #Stitch final video output with the audio 
    # stitch_all_audios(individual_directory_name)

    # # Create substitles based on extracted audio words.
    try:
        # Extract words from the extracted audio
        if not (os.path.isfile(extract_words_filepath)):
            extract_words(cropped_video_audio_extract_path, extract_words_filepath, DIMENSION)
    except Exception as e:
        print(f"Error found while extracting words from audio {filename}: {e}")
        raise e



    # Clean up temporary audio, temp video and subtitles directory
    print(f'Video processed and optimized')

def video_process_helper(individual_directory_name,index,processed_path, segments, cropped_video_path, cropped_video_path_segments, filename, isNextIndexImage):
    # If isNextIndexImage is true and current action is image then in both case extend the end to have extra 1 second to compensate for transition.
    try:
        uniqueFileName = individual_directory_name +'_' + str(index) + '.mp4'
        reels_processed_directory = os.path.join(processed_path, uniqueFileName)
        
        if os.path.exists(reels_processed_directory):
            return
        print(f"os path exist: {reels_processed_directory}")
        # Crop the already cropped video and do the following
        action = segments['action']
        if action == "IMAGE":
            isNextIndexImage = True
        start_time_sec = segments['start']
        end_time_sec = segments['end'] if not isNextIndexImage else segments['end'] + 1.00
        duration = end_time_sec - start_time_sec
        
        if action == "IMAGE":
            handle_image_action(segments['text'], IMAGE_GENERATION_DIR, reels_processed_directory, duration)
        else:
            # Sentence to input as prompt for image generation
            # image_prompt = f"In a {firstTwoSeg['emotion']} emotion and with a {firstTwoSeg['sentiment']} sentiment, the scene is {firstTwoSeg['text']}" 
            
            #Crop video based on start and end time of the segment
            crop_video(cropped_video_path, cropped_video_path_segments, start_time_sec, end_time_sec)
            
            # Extract and process frames in the frames folder
            extract_and_process_frames(cropped_video_path_segments, FRAMES_FOLDER_DIR, action)

            # Combine processed frames into a video
            create_video_from_frames(reels_processed_directory, FRAMES_FOLDER_DIR)

            for file in os.listdir(FRAMES_FOLDER_DIR):
                os.remove(os.path.join(FRAMES_FOLDER_DIR, file))
            
            #Remove Cropped segment video 
            os.remove(cropped_video_path_segments)
            

    except Exception as e:
        print(f"Error found while extracting and processing video {filename}: {e}")
        raise e

def stitch_video_output(individual_directory_name, processed_path):

    TRANSITIONS_DIR = os.path.join(PROCESSED_VIDEO_DIR, "transitions")
    final_video_filename = f"{individual_directory_name}.mp4"
    video_output_path = os.path.join(FINAL_VIDEO_DIR, final_video_filename)

    # Remove the file if already
    if(os.path.exists(video_output_path)):
        os.remove(video_output_path)

    video_files_unsorted = [f for f in os.listdir(processed_path) if f.endswith(".mp4")]
    video_files = sorted(video_files_unsorted, key=lambda f: int(re.search(r'_(\d+)\.mp4$', f).group(1)))

    # Initialize the output path for the first video
    current_output_path = os.path.join(processed_path, video_files[0])

    # Create a text file with video file list
    concatInputs = []
    print(f"STARTING TO CONCATTTT...............")
    try:
        # Write the first video file
        current_output_path = os.path.join(processed_path, video_files[0])
        first_video_duration = get_duration(current_output_path)
        temp_output = os.path.join(TEMPORARY_ACTIONS, "temp_file.mp4")
        add_silence(current_output_path, temp_output, first_video_duration)
        print(f"current_output_path {current_output_path}")

        # Remove the original file and rename the new file to the original name
        os.remove(current_output_path)
        os.rename(temp_output, current_output_path)
        concatInputs.append(current_output_path)
        
        files_to_skip = -1  # Number to always satisfy true at first
        for index in range(len(video_files) - 1):
            next_input_path = os.path.join(processed_path, video_files[index + 1])

            if not os.path.isfile(next_input_path):
                print(f"Warning: Next video file not found: {next_input_path}")
                continue

            if index + 1 > files_to_skip:
                # Check for transition files
                is_transition_included = None
                for transition_file in os.listdir(TRANSITIONS_DIR):
                    basename, _ = os.path.splitext(transition_file)
                    parts = basename.split("_")
                    numbersArray = parts[-1].split("-")
                    print(f"parts[-1] {parts[-1]}")
                    print(index + 1)
                    if str(index + 1) in numbersArray:
                        transition_file_path = os.path.join(
                            TRANSITIONS_DIR, transition_file
                        )
                        next_input_path = transition_file_path
                        files_to_skip = int(numbersArray[-1])
                        print(f"Files to skip: {files_to_skip}")

                        # Write to the text file
                        concatInputs.append(next_input_path)
                        is_transition_included = True
                        break
                print(f"is_transition_included: {is_transition_included}")
                print(f"next_input_path: {next_input_path}")
                print(f"next_input_path: {has_audio_track(next_input_path)}")
                if not is_transition_included:
                    if not has_audio_track(next_input_path):
                        duration = get_duration(next_input_path)
                        temp_output = os.path.join(TEMPORARY_ACTIONS, "temp_file.mp4")
                        add_silence(next_input_path, temp_output, duration)
                        print(f"current_output_path {next_input_path}")

                        # Remove the original file and rename the new file to the original name
                        os.remove(next_input_path)
                        os.rename(temp_output, next_input_path)
                    concatInputs.append(next_input_path)

    except Exception as e:
        print(f"Error writing file list: {e}")
        return
    print(f"concatInputs: {concatInputs}")
    filter_complex = ""
    input_options = ""
    for i, file in enumerate(concatInputs):
        input_options += f"-i {file} "
        filter_complex += f"[{i}:v:0][{i}:a:0]"

    # Add the concat filter
    filter_complex += f"concat=n={len(concatInputs)}:v=1:a=1[v][a]"

    # Full FFmpeg command
    command = (
        f'ffmpeg {input_options} -filter_complex "{filter_complex}" '
        f"-map [v] -map [a] -c:v libx264 -preset veryslow -c:a aac -b:a 192k {video_output_path}"
    )

    # Run the FFmpeg command
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running ffmpeg: {result.stderr}")
        else:
            print("Videos stitched successfully!")
    except Exception as e:
        print(f"An error occurred while running ffmpeg: {e}")

def handle_image_action (text, image_gen_dir, reels_processed_dir, duration):
    global DIMENSION, BASE_FILENAME
    print(f"DIMENSION{DIMENSION}")
    random_file_path = None
    try:
        keywords = ["business", "crypto", "money", "poor", "rich", "statistics"]
        classification = zero_shot_indentify(text, keywords)
        asset_tracker_result = asset_tracker('image', BASE_FILENAME)
        all_files = os.listdir(image_gen_dir + '/' + classification["labels"][0])
        filtered_files = [f for f in all_files if f not in asset_tracker_result]
        random_file = random.choice(filtered_files)
        asset_keeper('image', BASE_FILENAME, random_file)
        random_file_path = os.path.join(image_gen_dir + '/' + classification["labels"][0], random_file)
        # Create animation based on generated image
        animate_image(random_file_path, reels_processed_dir, duration, DIMENSION)
    except Exception as e:
        print(f"Error found while handle_image_action from random_file_path {random_file_path}: {e}")
        raise e
    
