from flask import Blueprint, request, jsonify
from controllers.action_controllers import (transcribe_controller, intent_identify_controller, emotion_analysis_controller, generate_subtitles_controller, 
    blueprint_process_controller, convert_fps_controller, generate_image_controller, animate_image_controller)

action_routes = Blueprint('Action Routes', __name__)

@action_routes.route("/transcribe_audio", methods=["POST"])
def transcribe_audio():
    data = request.get_json()
    transcribe_controller(data)

@action_routes.route("/intent_identify", methods=["POST"])
def indent_identify():
    data = request.get_json() 
    intent_identify_controller(data)

@action_routes.route("/emotion_analysis", methods=["POST"])
def emotion_analysis():
    data = request.get_json()  
    emotion_analysis_controller(data)

@action_routes.route("/generate_subtitles", methods=["POST"])
def insert_subtitles():
    data = request.get_json()  
    generate_subtitles_controller(data)

@action_routes.route("/blueprint_process", methods=["POST"])
def blueprint_process():
    data = request.get_json()
    blueprint_process_controller(data)

@action_routes.route("/animate_image", methods=["POST"])
def animate_image():
    data = request.get_json()
    animate_image_controller(data)

# @action_routes.route("/generate_image", methods=["POST"])
# def generate_image():
#     data = request.get_json()
#     generate_image_controller(data)

@action_routes.route("/convert_fps", methods=["POST"])
def convert_fps():
    data = request.get_json()
    convert_fps_controller(data)

@action_routes.before_request
def validate_request_payload():
    """Validate required parameters in the request payload."""
    data = request.get_json()

    if data is None:
        return jsonify({"error": "Request payload must be JSON"}), 400

    required_params = {
        "filename": "Filename parameter is required",
        "action_type": "Action Type parameter is required",
        "channel_niche": "Channel Niche parameter is required"
    }

    for param, error_message in required_params.items():
        if param not in data or not data[param]:
            return jsonify({"error": error_message}), 400

    return None  # No errors