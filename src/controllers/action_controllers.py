import os
from flask import jsonify

# Import packages
from app_package.helpers.directory_helper import REELS_BLUEPRINT, CONVERTED_FPS_DIR, SUBTITLES_PATH_DIR, WORDS_EXTRACTION_DIR, EXTRACT_AUDIO_DIR, TRANSCRIBED_DIR, INTENT_IDENTIFY_DIR, RAW_VIDEO_DIR

from app_package.transcribe_audio.main import link_to_reels_action_transcribe_audio
from app_package.intent_identifier.main import link_to_reels_action_intent_identifier
from app_package.emotion_analysis.main import link_to_reels_action_emotion_analysis
from app_package.generate_subtitles.main import link_to_reels_action_generate_subtitles
from app_package.blueprint_process.main import link_to_reels_action_blueprint_process
from app_package.convert_fps.main import link_to_reels_action_convert_fps


def handle_action(action_function, args, logging_object):
    if not action_function(*args):
        print(f"Error@controllers.{action_function} :: Action failed :: payload: {logging_object}")
        return jsonify(f"Error@controllers.{action_function} :: Action failed :: payload: {logging_object}"), 400
    return jsonify(f"success@controllers.{action_function} :: Action complete :: payload: {logging_object}"), 200

def transcribe_controller(data):
    filename = data.get("filename")
    action_type = data.get("action_type")
    channel_niche = data.get("channel_niche")
    
    basename, _ = os.path.splitext(filename)
    logging_object = {"filename": filename, "action_type": action_type, "channel_niche": channel_niche}

    try:
        #Check required dependencies exist or not.
        converted_fps_filepath = os.path.join(CONVERTED_FPS_DIR, f"{basename}.avi")
        if not os.path.exists(converted_fps_filepath):
            print(f"Error@controllers.transcribe_controller :: Provided filepath doesnt exist :: payload: {logging_object, f"converted_fps_filepath: {converted_fps_filepath}"}")
            return jsonify(f"Error@controllers.transcribe_controller :: No transcribed JSON file found for the filename :: payload: {logging_object}"), 400
        
        if action_type == "LINK_TO_REELS":
            return handle_action(link_to_reels_action_transcribe_audio, [basename, converted_fps_filepath, logging_object], logging_object)
    except Exception as e:
        print(f"Error@controllers.transcribe_controller :: Internal server error :: error: {e}, payload: {logging_object}")
        return jsonify(f"Error@controllers.transcribe_controller :: Internal server error :: error: {e}, payload: {logging_object}"), 500

def intent_identify_controller(data):
    filename = data.get("filename")
    action_type = data.get("action_type")
    channel_niche = data.get("channel_niche")

    basename, _ = os.path.splitext(filename)
    logging_object = {"filename": filename, "action_type": action_type, "channel_niche": channel_niche}

    try:
        #Check required dependencies exist or not.
        transcribed_filepath = os.path.join(TRANSCRIBED_DIR, f"{basename}.json")
        intent_identify_filepath = os.path.join(INTENT_IDENTIFY_DIR, f"{basename}.json")

        if not os.path.exists(transcribed_filepath):
            print(f"Error@controllers.intent_identify_controller :: No transcribed JSON file found for the filename :: payload: {logging_object}")
            return jsonify(f"Error@controllers.intent_identify_controller :: No transcribed JSON file found for the filename :: payload: {logging_object}"), 400
        if os.path.exists(intent_identify_filepath):
            print(f"Error@controllers.intent_identify_controller :: Filepath already exist :: payload: {logging_object}")
            return jsonify(f"Error@controllers.intent_identify_controller :: Filepath already exist :: payload: {logging_object}"), 400
        
        if action_type == "LINK_TO_REELS":
            return handle_action(link_to_reels_action_intent_identifier, [transcribed_filepath, intent_identify_filepath, channel_niche, logging_object], logging_object)
    except Exception as e:
        print(f"Error@controllers.intent_identify_controller :: Internal server error :: error: {e}, payload: {logging_object}")
        return jsonify(f"Error@controllers.intent_identify_controller :: Internal server error :: error: {e}, payload: {logging_object}"), 500

def emotion_analysis_controller(data):
    segment = data.get("segment")
    if not segment:
        return jsonify(f"Error@controllers.emotion_analysis_controller :: Segment value is required :: payload: {logging_object}"), 400

    filename = data.get("filename")
    action_type = data.get("action_type")
    channel_niche = data.get("channel_niche")

    basename, _ = os.path.splitext(filename)
    logging_object = {"filename": filename, "action_type": action_type, "channel_niche": channel_niche, "segment": segment}

    try:
        if action_type == "LINK_TO_REELS":
            return handle_action(link_to_reels_action_emotion_analysis, [segment, logging_object], logging_object)
    except Exception as e:
        print(f"Error@controllers.emotion_analysis_controller :: Internal server error :: error: {e}, payload: {logging_object}")
        return jsonify(f"Error@controllers.emotion_analysis_controller :: Internal server error :: error: {e}, payload: {logging_object}"), 500

def generate_subtitles_controller(data):
    filename = data.get("filename")
    action_type = data.get("action_type")
    channel_niche = data.get("channel_niche")

    basename, _ = os.path.splitext(filename)
    logging_object = {"filename": filename, "action_type": action_type, "channel_niche": channel_niche}

    try:
        #Check required dependencies exist or not.
        ass_filepath = os.path.join(SUBTITLES_PATH_DIR, f"{basename}.ass")
        extracted_words_filepath = os.path.join(WORDS_EXTRACTION_DIR, filename)
        if not os.path.exists(extracted_words_filepath):
            print(f"Error@controllers.generate_subtitles_controller :: Provided filepath doesnt exist :: payload: {logging_object, f"extracted_words_filepath":{extracted_words_filepath}}")
            return jsonify(f"Error@controllers.generate_subtitles_controller :: Provided filepath doesnt exist :: payload: {logging_object, f"extracted_words_filepath":{extracted_words_filepath}}"), 400
        if os.path.exists(ass_filepath):
            print(f"Error@controllers.generate_subtitles_controller :: Filepath already exist :: payload: {logging_object, f"ass_filepath: {ass_filepath}"}")
            return jsonify(f"Error@controllers.generate_subtitles_controller :: Filepath already exist :: payload: {logging_object, f"ass_filepath: {ass_filepath}"}"), 400
        
        if action_type == "LINK_TO_REELS":
            return handle_action(link_to_reels_action_generate_subtitles, [ass_filepath, extracted_words_filepath, logging_object], logging_object)
    except Exception as e:
        print(f"Error@controllers.generate_subtitles_controller :: Internal server error :: error: {e}, payload: {logging_object}")
        return jsonify(f"Error@controllers.generate_subtitles_controller :: Internal server error :: error: {e}, payload: {logging_object}"), 500
    
def blueprint_process_controller(data):
    filename = data.get("filename")
    action_type = data.get("action_type")
    channel_niche = data.get("channel_niche")
    video_filename = data.get("video_filename")

    basename, _ = os.path.splitext(filename)
    logging_object = {"filename": filename, "action_type": action_type, "channel_niche": channel_niche, "video_filename": video_filename}

    try:
        #Check required dependencies exist or not.
        reels_blueprint_filepath = os.path.join(REELS_BLUEPRINT, filename)
        video_filepath = os.path.join(CONVERTED_FPS_DIR, video_filename)

        for path in [reels_blueprint_filepath, video_filepath]:
            if not os.path.exists(path):
                print(f"Error@controllers.blueprint_process_controller :: Provided filepath doesnt exist :: payload: {logging_object, f"path: {path}"}")
                return jsonify(f"Error@controllers.blueprint_process_controller :: Provided filepath doesnt exist :: payload: {logging_object, f"path: {path}"}"), 400

        if action_type == "LINK_TO_REELS":
            return handle_action(link_to_reels_action_blueprint_process, [basename, reels_blueprint_filepath, video_filepath, logging_object], logging_object)
    except Exception as e:
        print(f"Error@controllers.blueprint_process_controller :: Internal server error :: error: {e}, payload: {logging_object}")
        return jsonify(f"Error@controllers.blueprint_process_controller :: Internal server error :: error: {e}, payload: {logging_object}"), 500
    
def convert_fps_controller(data):
    filename = data.get("filename")
    action_type = data.get("action_type")
    channel_niche = data.get("channel_niche")
    FPS = data.get("fps")

    basename, _ = os.path.splitext(filename)
    logging_object = {"filename": filename, "action_type": action_type, "channel_niche": channel_niche, "fps": FPS}
    
    if not FPS:
        return jsonify(f"Error@controllers.convert_fps_controller :: FPS value is required :: payload: {logging_object}"), 400


    try:
        #Check required dependencies exist or not.
        raw_video_filepath = os.path.join(RAW_VIDEO_DIR, filename)
        converted_filepath = os.path.join(CONVERTED_FPS_DIR, f"{basename}.avi")

        if not os.path.exists(raw_video_filepath):
            print(f"Error@controllers.convert_fps_controller :: Provided filepath doesnt exist :: payload: {logging_object, f"raw_video_filepath: {raw_video_filepath}"}")
            return jsonify(f"Error@controllers.convert_fps_controller :: Provided filepath doesnt exist :: payload: {logging_object, f"raw_video_filepath: {raw_video_filepath}"}"), 400
        if os.path.exists(converted_filepath):
            print(f"Error@controllers.convert_fps_controller :: Provided filepath already exist :: payload: {logging_object, f"converted_filepath: {converted_filepath}"}")
            return jsonify(f"Error@controllers.convert_fps_controller :: Provided filepath already exist :: payload: {logging_object, f"converted_filepath: {converted_filepath}"}"), 400
    
        if action_type == "LINK_TO_REELS":
            return handle_action(link_to_reels_action_convert_fps, [raw_video_filepath, converted_filepath, FPS, logging_object], logging_object)
    except Exception as e:
        print(f"Error@controllers.convert_fps_controller :: Internal server error :: error: {e}, payload: {logging_object}")
        return jsonify(f"Error@controllers.convert_fps_controller :: Internal server error :: error: {e}, payload: {logging_object}"), 500
