from models.emotion_analysis_model import emotion_analysis

def link_to_reels_action_emotion_analysis(segment, logging_object):
    try:
        emotion_analysis_response = emotion_analysis(segment)
        if not emotion_analysis_response:
            return False
        return emotion_analysis_response
    except Exception as e:
        print(f"Error@emotion_analysis.link_to_reels_action_emotion_analysis :: Error performing emotion analysis :: error: {e}, payload: {logging_object}")
        return False