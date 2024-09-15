import os

# Define the base directory as the directory containing this file
BASE_DIR = os.path.dirname(__file__)

# Define directory paths relative to the base directory
AUDIO_DIR = os.path.join(BASE_DIR, "../../audio_files")
TRANSCRIBED_DIR = os.path.join(BASE_DIR, "../../transcribed_audio")
RAW_TRANSCRIBED_DIR = os.path.join(BASE_DIR, "../../raw_transcribed_audio")
INTENT_IDENTIFY_DIR = os.path.join(BASE_DIR, "../../intent-identify")
RAW_VIDEO_DIR = os.path.join(BASE_DIR, "../../raw_video")
PROCESSED_VIDEO_DIR = os.path.join(BASE_DIR, "../../processed_video")
SUBTITLES_PATH_DIR = os.path.join(BASE_DIR, "../../subtitles")
FRAMES_FOLDER_DIR = os.path.join(BASE_DIR, "../../frames_folder")
REELS_BLUEPRINT = os.path.join(BASE_DIR, "../../reels_blueprint")
CROPPED_VIDEO_DIR = os.path.join(BASE_DIR, "../../cropped_video")
IMAGE_GENERATION_DIR = os.path.join(BASE_DIR, "../../image-generation")
WORDS_EXTRACTION_DIR = os.path.join(BASE_DIR, "../../extracted_words")
SOUND_EFFECTS_DIR = os.path.join(BASE_DIR, "../../sound_effects")
FINAL_VIDEO_DIR = os.path.join(BASE_DIR, "../../video_output")
SONGS_DIR = os.path.join(BASE_DIR, "../../songs")
TEMPORARY_ACTIONS = os.path.join(BASE_DIR, "../../temporary_actions")
TRACK_ASSETS = os.path.join(BASE_DIR, "../../track_assets")