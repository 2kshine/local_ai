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
import os

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
PROCESSED_FRAMES_FOLDER_DIR = os.path.join(os.path.dirname(__file__), "../processed_frames_folder")

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
        transcribe_audio(audio_data, filename,TRANSCRIBED_DIR, RAW_TRANSCRIBED_DIR)

        return jsonify({"message":"Audio file transcription complete"}), 200

    except Exception as e:
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
    reels_script = data.get("reels_script")  # Extract 'segment'
    filename = data.get("filename")  # Extract 'segment'

    if not reels_script:
        return jsonify({"error": "Reels script is required"}), 400

    try:
        processedVideo = video_process(RAW_VIDEO_DIR, PROCESSED_VIDEO_DIR, filename, reels_script[1], FRAMES_FOLDER_DIR, PROCESSED_FRAMES_FOLDER_DIR)
        return jsonify(), 200


    except Exception as e:
        return jsonify({"/videoProcessor error:": str(e)}), 500

@app.route("/insert_subtitles", methods=["POST"])
def insertSubtitles():

    data = request.get_json()  # Get JSON body
    reels_script = data.get("reels_script")  # Extract 'subtitles'
    filename = data.get("filename")  # Extract 'subtitles'

    if not reels_script:
        return jsonify({"error": "Reels script is required"}), 400

    try:
        # Generate Ass subtitles 
        subtitles_essentials = reels_script[0]
        basename, ext = os.path.splitext(filename)
        ass_file = SUBTITLES_PATH_DIR + f"/{basename + '_subtitles' + '.ass'}"   
        final_output = PROCESSED_VIDEO_DIR + f"/{basename + '_final_output' + ext}" # Path to the final video 
        cropped_video = PROCESSED_VIDEO_DIR + f"/{basename + '_cropped' + ext}" # Path to the cropped video
        generate_subtitles(subtitles_essentials, ass_file)

        add_subtitles(cropped_video, ass_file, final_output)
        return jsonify(), 200
    except Exception as e:
        return jsonify({"/videoProcessor error:": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
