import os
import numpy as np
from PIL import Image, ImageOps
from moviepy.editor import VideoFileClip, ImageSequenceClip
import random
import json
import subprocess

from app_package.split_av import (
    splitAV_func
)
from app_package.image_generation import (
    animate_image
)

from app_package.helpers import (
    detect_people,
    get_focus_box,
    resize_for_tiktok
)

from app_package.intent_identifier import (
    zero_shot_indentify
)
from app_package.transcriber import (
    extract_words
)
from app_package.stitch_transition import (
    stitch_transition
)

GLOBAL_FOCUS_BOX = None
REEL_HEIGHT = None
REEL_WIDTH = None
ACTION_STATUS = None
DIMENSION=None
def zoom_in_from_sides_except_top(img, zoom_factor):
    # Open the image
    original_width, original_height = img.size

    # Calculate new dimensions
    new_width = int(original_width * zoom_factor)
    new_height = int(original_height * zoom_factor)

    # Resize the image
    resized_img = img.resize((new_width, new_height), Image.LANCZOS)

    # Calculate cropping box to crop from the top and sides
    left = (new_width - original_width) // 2
    top = 0
    right = left + original_width
    bottom = original_height

    # Crop the image
    cropped_img = resized_img.crop((left, top, right, bottom))

    return cropped_img

def crop_frame(frame, focus_box):
    """Crop the frame based on focus box."""
    x_min, y_min, x_max, y_max = focus_box
    cropped = frame[y_min:y_max, x_min:x_max]
    return cropped

def ensure_even_dimensions(image):
    width, height = image.size
    # Adjust dimensions to be divisible by 2
    if width % 2 != 0:
        width -= 1
    if height % 2 != 0:
        height -= 1
    return image.resize((width, height)).convert('RGB')

def extract_and_process_frames(video_path, frames_dir, action):
    try:
        global GLOBAL_FOCUS_BOX
        """Extract and process frames: detect people, apply random zoom effects, resize for TikTok, and save the frame."""
        clip = VideoFileClip(video_path)
        fps = 30
        duration = clip.duration
        frame_count = int(duration * fps)
        
        for t in range(frame_count):
            frame = clip.get_frame(t / fps)
            frame = np.array(frame)
            people_boxes = detect_people(frame)
            
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

                frame_path = os.path.join(frames_dir, f'frame_{t:04d}.png')

                if(action == "ZOOM"):
                    tiktok_ready_image = resize_for_tiktok(image)
                    zoomed_image = zoom_in_from_sides_except_top(tiktok_ready_image, 1.2)
                    zoomed_image_ensure = ensure_even_dimensions(zoomed_image) #make sure its divisible int
                    zoomed_image_ensure.save(frame_path, format='PNG', quality=100)

                else:
                    tiktok_ready_image = resize_for_tiktok(image)
                    tiktok_ready_image_ensure = ensure_even_dimensions(tiktok_ready_image) #make sure its divisible int
                    tiktok_ready_image_ensure.save(frame_path, format='PNG', quality=100)

                # Resize for TikTok aspect ratio
                
                # Save processed frame
            else: #Return so that we can put in image instead of people less reel
                # Save original frame if no people are detected
                image = Image.fromarray(frame)
                tiktok_ready_image = resize_for_tiktok(image)
                image_ensure = ensure_even_dimensions(tiktok_ready_image)
                frame_path = os.path.join(frames_dir, f'frame_{t:04d}.png')
                image_ensure.save(frame_path, format='PNG', quality=100)
    
    except Exception as e:
        print(f"Error found while cropping video from extract_and_process_frames for video_path {video_path}: {e}")
        raise e

def create_video_from_frames(output_video_path, frames_dir):
    global DIMENSION
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
            DIMENSION = clip.size
        else:
            print("No frames available to create the video.")
    except Exception as e:
        print(f"Error found while cropping video from create_video_from_frames for output_video_path {output_video_path}: {e}")
        raise e
    
def get_video_bitrate(file_path):
    # Run ffprobe to get video information
    command = [
        'ffprobe', 
        '-v', 'error', 
        '-select_streams', 'v:0', 
        '-show_entries', 'stream=bit_rate', 
        '-of', 'json',
        file_path
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    data = json.loads(result.stdout)
    
    if 'streams' in data and len(data['streams']) > 0:
        bitrate = data['streams'][0].get('bit_rate')
        if bitrate:
            # Convert bitrate to kilobits per second (kbps)
            return int(bitrate) // 1000
    return None

def crop_video(input_file, output_file, start_time_sec, end_time_sec):
    try:
        # Get the original bitrate
        original_bitrate = get_video_bitrate(input_file)
        if original_bitrate is None:
            raise ValueError("Could not determine the original bitrate.")
        
        # Set a high bitrate for HD quality
        # Typical bitrates for HD quality: 720p ~ 5 Mbps, 1080p ~ 10 Mbps
        target_bitrate = '10000k'  # 10 Mbps for 1080p HD
        bufsize = f"{2 * int(target_bitrate[:-1])}k"  # Dynamic buffer size
        
        # Load the video clip
        clip = VideoFileClip(input_file)
        
        # Crop the clip based on the specified time range
        cropped_clip = clip.subclip(start_time_sec, end_time_sec)
        
        # Ensure the output resolution is HD (if necessary)
        # This ensures the output resolution is at least 1080p
        width, height = cropped_clip.size
        if width < 1920 or height < 1080:
            cropped_clip = cropped_clip.resize(newsize=(1920, 1080))

        # Set the desired frame rate
        fps = 30

        # Write the cropped clip to the output file with HD quality settings
        cropped_clip.write_videofile(
            output_file, 
            codec='libx264',
            fps=fps,  # Set frame rate to 30 fps
            preset='veryslow',  # Use 'veryslow' for better quality
            ffmpeg_params=[
                '-profile:v', 'high',
                '-b:v', target_bitrate,  # Set the bitrate for HD quality
                '-maxrate', target_bitrate,
                '-bufsize', bufsize  # Dynamic buffer size
            ],
        )
        
        # Close the clips to release resources
        clip.close()
        cropped_clip.close()

        print(f"Video cropped and saved to '{output_file}'.")
    except Exception as e:
        print(f"Error found while cropping video from input_file {input_file}: {e}")
        raise e

def handle_image_action (text, image_gen_dir, reels_processed_dir, duration):
    global DIMENSION
    print(f"DIMENSION{DIMENSION}")
    try:
        keywords = ["business", "crypto", "money", "poor", "rich", "statistics"]
        classification = zero_shot_indentify(text, keywords)
        all_files = os.listdir(image_gen_dir + '/' + classification["labels"][0])
        random_file = random.choice(all_files)
        random_file_path = os.path.join(image_gen_dir + '/' + classification["labels"][0], random_file)
        # Create animation based on generated image
        animate_image(random_file_path, reels_processed_dir, duration, DIMENSION)
    except Exception as e:
        print(f"Error found while handle_image_action from random_file_path {random_file_path}: {e}")
        raise e

def stitch_transition_helper(action_json, processed_path, individual_directory_name, transitions_directory):
    global ACTION_STATUS
    if not processed_path:
        raise ValueError("No video files found in the directory.")
    print(action_json)
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
                stitch_transition(str(index - 1), str(index), previousClip_directory, currentClip_directory, transitions_directory)
            ACTION_STATUS = action
    except Exception as e:
        print(f"Error stitching transaction helpers {processed_path}: {e}")
        raise e
# Main processing function
def video_process(input_video, cropped_video_dir, processed_video_dir, filename, reels_script_path, FRAMES_FOLDER_DIR, AUDIO_DIR, IMAGE_GENERATION_DIR, EXTRACTED_WORDS_DIR):

    # Load the json script 
    # Open the JSON file for reading
    with open(reels_script_path, 'r') as file:
        # Load JSON data from the file
        reels_script = json.load(file)
    reels_video_script = reels_script[0]
    reels_result_script = reels_script[1]

    basename, ext = os.path.splitext(filename)
    individual_directory_name = basename + '_' + reels_result_script['id']
    filename_unique = individual_directory_name + ext
    filename_unique_segments = individual_directory_name + '_cropped' + ext
    extract_audio_filename = individual_directory_name + '.mp3'
    extract_words_filename = individual_directory_name + '.json'

    # Crop the raw video according to the start time and end time seconds 
    cropped_video_path = os.path.join(cropped_video_dir, filename_unique)
    cropped_video_path_segments = os.path.join(cropped_video_dir, filename_unique_segments)
    processed_path = os.path.join(processed_video_dir, individual_directory_name)
    cropped_video_audio_extract_path = os.path.join(AUDIO_DIR, extract_audio_filename)
    extract_words_filepath = os.path.join(EXTRACTED_WORDS_DIR, extract_words_filename)
    transitions_directory = os.path.join(processed_video_dir, 'transitions')
    if not os.path.exists(processed_path):
        os.makedirs(processed_path)
    # If no directory in processed path for each reels create one 

    # try:
    #     # Crop the video to the specified time range if the file doesnt already exist
    #     if not (os.path.isfile(cropped_video_path)):
    #         start_time_sec = reels_result_script['results']['period']['startTime']
    #         end_time_sec = reels_result_script['results']['period']['endTime']
    #         crop_video(input_video, cropped_video_path, start_time_sec, end_time_sec)
    # except Exception as e:
    #     print(f"Error found while cropping {filename}: {e}")
    #     raise e
    
    # Get audio files to be transcribed in words 
    # try:
    #     # Split Audio and video of a raw video if the file doesnt already exist
    #     if not (os.path.isfile(cropped_video_audio_extract_path)):
    #         extractedAudioFilePath = splitAV_func(cropped_video_path, cropped_video_audio_extract_path)
    # except Exception as e:
    #     print(f"Error found while splitting cropped video to audio {filename}: {e}")
    #     raise e

    #Always set the first segment and last segment to be a Normal Action
    # reels_video_script[0]['action'] = "NORMAL"
    # reels_video_script[-1]['action'] = "NORMAL"
    
    # #Loop through each segment, check the action, ignore the first two segment and extract frames and process them 
    # for index, firstTwoSeg in enumerate(reels_video_script[:2]):
    #     video_process_helper(individual_directory_name,index,processed_path, firstTwoSeg, cropped_video_path, cropped_video_path_segments, FRAMES_FOLDER_DIR,IMAGE_GENERATION_DIR, filename)
    
    # for index, restSeg in enumerate(reels_video_script):
    #     video_process_helper(individual_directory_name,index,processed_path, restSeg, cropped_video_path, cropped_video_path_segments, FRAMES_FOLDER_DIR,IMAGE_GENERATION_DIR, filename)

    #Remove all cropped files 
    # for file in os.listdir(cropped_video_dir):
    #     os.remove(os.path.join(cropped_video_dir, file))

    # Figure out the transition times for all the video segments
    try:
        # Creating the action_json
        action_json = [
            entry.get('action')
            for entry in reels_video_script
        ]        
        stitch_transition_helper(action_json, processed_path, individual_directory_name, transitions_directory)
    except Exception as e:
        print(f"Error found while stitching transitions {filename}: {e}")
        raise e
    # Create substitles based on extracted audio words.
    # try:
    #     # Extract words from the extracted audio
    #     if not (os.path.isfile(extract_words_filepath)):
    #         extract_words(cropped_video_audio_extract_path, extract_words_filepath)
    # except Exception as e:
    #     print(f"Error found while extracting words from audio {filename}: {e}")
    #     raise e
    # Clean up temporary audio, temp video and subtitles directory

    # Based on emotions of the whole segment, add a song to it.

    print(f'Video processed and optimized')

def video_process_helper(individual_directory_name,index,processed_path, segments, cropped_video_path, cropped_video_path_segments, FRAMES_FOLDER_DIR,IMAGE_GENERATION_DIR, filename):
    try:
        uniqueFileName = individual_directory_name +'_' + str(index) + '.mp4'
        reels_processed_directory = os.path.join(processed_path, uniqueFileName)

        # Crop the already cropped video and do the following
        start_time_sec = segments['start']
        end_time_sec = segments['end']
        duration = segments['end'] - segments['start']
        action = segments['action']
        
        if action == "IMAGE":
            handle_image_action(segments['text'], IMAGE_GENERATION_DIR, reels_processed_directory, duration)
        else:
            # Sentence to input as prompt for image generation
            # image_prompt = f"In a {firstTwoSeg['emotion']} emotion and with a {firstTwoSeg['sentiment']} sentiment, the scene is {firstTwoSeg['text']}" 
            
            if not (os.path.isfile(cropped_video_path_segments)):
                #Crop video based on start and end time of the segment
                crop_video(cropped_video_path, cropped_video_path_segments, start_time_sec, end_time_sec)
            
            # Extract and process frames in the frames folder
            extract_and_process_frames(cropped_video_path_segments, FRAMES_FOLDER_DIR, action)

            if not (os.path.isfile(reels_processed_directory)):
                # Combine processed frames into a video
                create_video_from_frames(reels_processed_directory, FRAMES_FOLDER_DIR)

            for file in os.listdir(FRAMES_FOLDER_DIR):
                os.remove(os.path.join(FRAMES_FOLDER_DIR, file))

    except Exception as e:
        print(f"Error found while extracting and processing video {filename}: {e}")
        raise e
