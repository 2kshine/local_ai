from flask import Flask, request, jsonify
from src.routes.action_routes import action_routes

app = Flask(__name__)

# Register routes 
action_routes(app)

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

import os
import glob


from app_package.helpers.directory_helper import SUBTITLES_PATH_DIR, REELS_BLUEPRINT, WORDS_EXTRACTION_DIR





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
