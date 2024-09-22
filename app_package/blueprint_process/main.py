import os

from app_package.helpers.directory_helper import PROCESSED_VIDEO_DIR, CROPPED_VIDEO_DIR, TEMPORARY_ACTIONS, AUDIO_DIR, FRAMES_FOLDER_DIR
from app_package.helpers.json_action import read_json
from app_package.helpers.crop_video import crop_video
from app_package.helpers.extract_audio import extract_audio
from app_package.blueprint_process.helper import extract_frames
def link_to_reels_action_blueprint_process (basename, reels_blueprint_filepath, video_filepath, logging_object):
    # Read reels_blueprint_filepath of type json
    reels_script = read_json(reels_blueprint_filepath)
    reels_video_script = reels_script['payload']
    reels_result_script = reels_script

    individual_directory_name = basename + '_' + reels_result_script['id'] #directory name for processed video

    processed_path = os.path.join(PROCESSED_VIDEO_DIR, individual_directory_name)
    frames_processed_path = os.path.join(FRAMES_FOLDER_DIR, individual_directory_name)
    cropped_video_path = os.path.join(CROPPED_VIDEO_DIR, f"{individual_directory_name}.avi")
    cropped_video_extract_audio_path = os.path.join(AUDIO_DIR, f"{individual_directory_name}.wav")
    temporary_cropped_video_path = os.path.join(TEMPORARY_ACTIONS, f"{individual_directory_name}.avi")
    # If no directory in processed path for each reels create one 
    if not os.path.exists(processed_path):
        os.makedirs(processed_path)
    if not os.path.exists(frames_processed_path):
        os.makedirs(frames_processed_path)
    #Crop the video to the specified time range if the file doesnt already exist for processing videos.
    if not os.path.exists(cropped_video_path):
        start_time_sec = reels_result_script['results']['period']['startTime']
        end_time_sec = reels_result_script['results']['period']['endTime']
        if not crop_video(video_filepath, cropped_video_path, start_time_sec, end_time_sec):
            print(f"Error@blueprint_process.link_to_reels_action_blueprint_process :: Cropping failed :: payload: {logging_object, f"cropped_video_path: {cropped_video_path}"}")
            return False
        
    #Extract the audio for later joining after processing the video. 
    if not os.path.exists(cropped_video_extract_audio_path):
        if not extract_audio(cropped_video_path, cropped_video_extract_audio_path, False):
            return False
        
    # Always set the first segment and last segment to be a Normal Action
    reels_video_script[0]['action'] = "NORMAL"
    reels_video_script[1]['action'] = "NORMAL"
    reels_video_script[-1]['action'] = "NORMAL"
    
    for index, segment in enumerate(reels_video_script):
        action = segment['action']
        if action == "IMAGE":
            continue #Skip it
        isNextIndexImage = None
        # Check if the next index is Image 
        if (index + 1) < len(reels_video_script) and reels_video_script[(index + 1)]['action'] == "IMAGE":
            isNextIndexImage = True

        uniqueFileName = individual_directory_name +'_' + str(index) + '.mp4'
        reels_processed_directory = os.path.join(processed_path, uniqueFileName)
        if not os.path.exists(reels_processed_directory):
            print(f"Warning@blueprint_process.link_to_reels_action_blueprint_process :: Process file already exist.. Skipping :: payload: {logging_object, f"reels_processed_directory: {reels_processed_directory}"}")
            continue #Skip it

        start_time_sec = segment['start']
        end_time_sec = segment['end'] if not isNextIndexImage else segment['end'] + 1.00 # 1 becacuse it goes through transition.
        duration = end_time_sec - start_time_sec

        #Crop the video to the temporary folder
        if not crop_video(cropped_video_path, temporary_cropped_video_path, start_time_sec, end_time_sec):
            return False
        
        # Extract Frames to the individual frames folder
        if not extract_frames(temporary_cropped_video_path, frames_processed_path, action):
            return False
        

        #Remove the cropped video 
        os.remove(temporary_cropped_video_path)


        
    


    