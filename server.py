from flask import Flask, request, jsonify
from app_package.transcriber import (
    load_audio,
    transcribe_audio,
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
from app_package.final_reel_render import (
    final_reel_render
)
from app_package.split_av import (
    splitAV_func,
    convert_video_fps
)
import os
import glob

app = Flask(__name__)

from app_package.directory_helper import SUBTITLES_PATH_DIR, REELS_BLUEPRINT, WORDS_EXTRACTION_DIR

@app.route("/transcribe-audio", methods=["POST"])
def transcribe():

    data = request.get_json()  # Get JSON body
    filename = data.get("filename")  # Extract 'filename'

    if not filename:
        return jsonify({"error": "Filename parameter is required"}), 400

    try:

        # Load and process the audio file
        audio_data = load_audio(filename)

        #Transcribe audio
        transcribe_audio(audio_data, filename)

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

    try:
        classifier_func(filename)
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
    
    # Use glob to find all matching files
    matching_files = glob.glob(search_pattern)

    # Get the first file in the raw video dir
    for reels_script_path in matching_files:
        try:
            processedVideo = video_process(filename, reels_script_path)
            return jsonify({"filename": processedVideo}), 200
        except Exception as e:
            print(e)
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
        # Convert the raw video to 30 fps
        convert_video_fps(filename)

        # Split Audio and video of a raw video 
        splitAV_func(filename)
        return jsonify({"message": "Successfully converted video to 30 fps and splitted audio"}), 200
    except Exception as e:
        return jsonify({"/Failed raw video extraction error:": str(e)}), 500

@app.route("/reel_render", methods=["POST"])
def final_reel_render_handler():

    data = request.get_json()  # Get JSON body
    filename = data.get("filename")  # Extract 'subtitles'

    if not filename:
        return jsonify({"error": "Filename is required"}), 400

    try:
        # Final reel render with subtitles.
        final_reel_render(filename)
        return jsonify({"message": "Reels rendered successfully"}), 200
    except Exception as e:
        print(e)
        return jsonify({"/Failed raw video extraction error:": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
