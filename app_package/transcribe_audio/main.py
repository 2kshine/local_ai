import os
from app_package.helpers.directory_helper import TRANSCRIBED_DIR, RAW_TRANSCRIBED_DIR, WORDS_EXTRACTION_DIR, EXTRACT_AUDIO_DIR
from app_package.helpers.json_action import write_json
from app_package.helpers.extract_audio import extract_audio

from models.transcribe_audio_model import transcribe_audio

def link_to_reels_action_transcribe_audio(basename, converted_fps_filepath, logging_object):
    # Filepath specification
    file_paths = {
        'split_audio': os.path.join(EXTRACT_AUDIO_DIR, f"{basename}.wav"),
        'raw_transcribed': os.path.join(RAW_TRANSCRIBED_DIR, f"{basename}.txt"),
        'transcribed': os.path.join(TRANSCRIBED_DIR, f"{basename}.json"),
        'extracted_words': os.path.join(WORDS_EXTRACTION_DIR, f"{basename}.json")
    }

    # Check if files already exist
    for f in file_paths.values():
        if os.path.exists(f):
            print(f"Error@transcribe_audio.link_to_reels_action_transcribe_audio :: File already exists, delete the file to rerun the action :: payload: {logging_object, f"file_paths: {f}"}")
            return False

    # Extract audio from converted fps audio
    if not extract_audio(converted_fps_filepath, file_paths['split_audio'], True):
        return False
    
    # Initialize data objects
    data_for_extracted_words = {"subtitles": []}
    data_for_transcribed_audio = []
    long_chunk_transcribed_audio = None

    try:
        # Run the model
        transcribedWords = transcribe_audio(file_paths['split_audio'])
        if not transcribedWords:
            return False

        # Process the results
        for segment in transcribedWords['segments']:
            # For transcribed audio to be processed in node side
            data_for_transcribed_audio.append({
                'text': segment['text'].strip(),
                'start': segment['start'],
                'end': segment['end']
            })
            
            # For subtitles to be processed later
            for word in segment['words']:
                data_for_extracted_words['subtitles'].append({
                    'text': word['text'].strip(),
                    'start': word['start'],
                    'end': word['end']
                })

        # For raw transcribed audio
        long_chunk_transcribed_audio = transcribedWords['text'].strip()

        # Prepare data for saving
        data_to_save = {
            file_paths['extracted_words']: data_for_extracted_words,
            file_paths['transcribed']: data_for_transcribed_audio,
            file_paths['raw_transcribed']: long_chunk_transcribed_audio
        }

        # Save all files
        for path, data in data_to_save.items():
            if not write_json(data, path):
                print(f"Error@transcribe_audio.link_to_reels_action_transcribe_audio :: Failed to write the output to the json file: Delete it and retry: Filename path :: payload: {logging_object, f"file_paths: {path}"}")
                return False
        
        return True
    except Exception as e:
        print(f"Error@transcribe_audio.link_to_reels_action_transcribe_audio :: Error transcribing :: error: {e}, payload: {logging_object}")
        return False
    finally:
        os.remove(file_paths['split_audio'])