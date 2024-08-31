from flask import Flask, request, jsonify
from app_package.transcriber import (
    load_audio,
    transcribe_audio,
    save_transcription,
)
from app_package.intent_identifier import (
    classifier_func
)
from app_package.emotion_analysis import (
    emotion_func
)
from app_package.video_process import (
    video_process,
)
from app_package.insert_subtitles import (
    generate_subtitles,
    add_subtitles
)
from app_package.split_av import (
    splitAV_func
)
import os
import glob

app = Flask(__name__)

# Define the directory where audio files will be read from
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "../audio_files")
TRANSCRIBED_DIR = os.path.join(os.path.dirname(__file__), "../transcribed_audio")
RAW_TRANSCRIBED_DIR = os.path.join(os.path.dirname(__file__), "../raw_transcribed_audio")
INTENT_IDENTIFY_DIR = os.path.join(os.path.dirname(__file__), "../intent-identify")
RAW_VIDEO_DIR = os.path.join(os.path.dirname(__file__), "../raw_video")
PROCESSED_VIDEO_DIR = os.path.join(os.path.dirname(__file__), "../processed_video")
SUBTITLES_PATH_DIR = os.path.join(os.path.dirname(__file__), "../subtitles")
FRAMES_FOLDER_DIR = os.path.join(os.path.dirname(__file__), "../frames_folder")
REELS_BLUEPRINT = os.path.join(os.path.dirname(__file__), "../reels_blueprint")
CROPPED_VIDEO_DIR = os.path.join(os.path.dirname(__file__), "../cropped_video")
IMAGE_GENERATION_DIR = os.path.join(os.path.dirname(__file__), "../image-generation")
WORDS_EXTRACTION_DIR = os.path.join(os.path.dirname(__file__), "../extracted_words")
SOUND_EFFECTS_DIR = os.path.join(os.path.dirname(__file__), "../sound_effects")

@app.route("/transcribe-audio", methods=["POST"])
def transcribe():

    data = request.get_json()  # Get JSON body
    filename = data.get("filename")  # Extract 'filename'

    if not filename:
        return jsonify({"error": "Filename parameter is required"}), 400

    file_path = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        # Load and process the audio file
        audio_data = load_audio(file_path)

        #Transcribe audio
        transcribe_audio(audio_data, filename, TRANSCRIBED_DIR, RAW_TRANSCRIBED_DIR)

        return jsonify({"message":"Audio file transcription complete"}), 200

    except Exception as e:
        print (e)
        return jsonify({"/transcribe-audio error:": str(e)}), 500

@app.route("/intent-identify", methods=["POST"])
def intentIdentifier():

    data = request.get_json()  # Get JSON body
    filename = data.get("filename")  # Extract 'filename'

    if not filename:
        return jsonify({"error": "Filename parameter is required"}), 400

    file_path = os.path.join(TRANSCRIBED_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        classifier_func(filename, file_path, INTENT_IDENTIFY_DIR)
        return jsonify(), 200

    except Exception as e:
        return jsonify({"/transcribe-audio error:": str(e)}), 500

@app.route("/emotion-analysis", methods=["POST"])
def emotionAnalyser():

    data = request.get_json()  # Get JSON body
    segment = data.get("segment")  # Extract 'segment'

    if not segment:
        return jsonify({"error": "Segment value is required"}), 400

    try:
        analysedEmotion = emotion_func(segment)
        return jsonify(analysedEmotion), 200


    except Exception as e:
        return jsonify({"/emotionAnalyser error:": str(e)}), 500

@app.route("/video_process", methods=["POST"])
def videoProcessor():

    data = request.get_json()  # Get JSON body
    filename = data.get("filename")  # Extract 'segment'
    # Create a search pattern
    basename, _ = os.path.splitext(filename)
    search_pattern = os.path.join(REELS_BLUEPRINT, f'*{basename}*')
    raw_video_file = os.path.join(RAW_VIDEO_DIR, filename)
    
    # Use glob to find all matching files
    matching_files = glob.glob(search_pattern)

    # Get the first file in the raw video dir
    for reels_script_path in matching_files:
        try:
            processedVideo = video_process(raw_video_file, CROPPED_VIDEO_DIR, PROCESSED_VIDEO_DIR, filename, reels_script_path, FRAMES_FOLDER_DIR, AUDIO_DIR, IMAGE_GENERATION_DIR, WORDS_EXTRACTION_DIR)
            return jsonify({"filename": processedVideo}), 200
        except Exception as e:
            return jsonify({"/videoProcessor error:": str(e)}), 500
    return jsonify(), 200
@app.route("/insert_subtitles", methods=["POST"])
def insertSubtitles():

    data = request.get_json()  # Get JSON body
    filename = data.get("filename")  # Extract 'subtitles'

    if not filename:
        return jsonify({"error": "Filename is required"}), 400

    try:
        # Generate Ass subtitles 
        basename, ext = os.path.splitext(filename)
        ass_file = SUBTITLES_PATH_DIR + f"/{basename + '.ass'}"   
        subtitles_data_filepath = os.path.join(WORDS_EXTRACTION_DIR, filename)
        generate_subtitles(subtitles_data_filepath, ass_file)

        return jsonify(), 200
    except Exception as e:
        return jsonify({"/Insert subtitles error:": str(e)}), 500
    
@app.route("/split_av", methods=["POST"])
def splitAV():

    data = request.get_json()  # Get JSON body
    filename = data.get("filename")  # Extract 'subtitles'

    if not filename:
        return jsonify({"error": "Filename is required"}), 400

    try:
        # Split Audio and video of a raw video 
        extractFileName = splitAV_func(RAW_VIDEO_DIR, AUDIO_DIR, filename)
        return jsonify({"audiofilename": extractFileName}), 200
    except Exception as e:
        return jsonify({"/Failed raw video extraction error:": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
