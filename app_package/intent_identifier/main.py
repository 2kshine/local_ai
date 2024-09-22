import os
from app_package.helpers.json_action import write_json, read_json
from models.transcribe_audio_model import intent_identify

def link_to_reels_action_intent_identifier(transcribed_filepath, intent_identify_filepath, channel_niche, logging_object):


    # Read the transcribed sentences
    sentence_list = read_json(transcribed_filepath)
    keywords = [channel_niche]
    results = []

    try:
        for sentence in sentence_list:
            # Run the intent identification model
            classification = intent_identify(sentence['text'], keywords)

            if not classification:
                print(f"Error@intent_identifier.link_to_reels_action_intent_identifier :: Failed to identify intents. Please delete the file and retry. :: payload: {logging_object}")
                return False

            # Enrich the sentence object with classification details
            enriched_sentence = {
                **sentence,
                'classification': {
                    "label": classification["labels"][0],
                    "score": classification["scores"][0]
                },
            }
            results.append(enriched_sentence)

        # Write the results to a JSON file
        if not write_json(results, intent_identify_filepath):
            print(f"Error@intent_identifier.link_to_reels_action_intent_identifier :: Failed to write the output to the JSON file. Please delete it and retry. :: payload: {logging_object, f"intent_identify_filepath: {intent_identify_filepath}"}")
            return False
        
        return True
    except Exception as e:
        print(f"Error@intent_identifier.link_to_reels_action_intent_identifier :: Error processing sentences :: error: {e}, payload: {logging_object}")
        return False

