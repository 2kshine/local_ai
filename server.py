from flask import Flask, request, jsonify
from app_package.transcriber import (
    load_audio,
    transcribe_audio,
    save_transcription,
)
from app_package.intent_identifier import (
    classifier_func
)
import os

app = Flask(__name__)

# Define the directory where audio files will be read from
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "../audio_files")
TRANSCRIBED_DIR = os.path.join(os.path.dirname(__file__), "../transcribed_audio")
RAW_TRANSCRIBED_DIR = os.path.join(os.path.dirname(__file__), "../raw_transcribed_audio")
INTENT_IDENTIFY = os.path.join(os.path.dirname(__file__), "../intent-identify")


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
        classifier_func(filename, file_path, INTENT_IDENTIFY)
        return jsonify(), 200

    except Exception as e:
        return jsonify({"/transcribe-audio error:": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
