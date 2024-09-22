import soundfile as sf
import numpy as np

def load_audio(audio_filepath):
    try:
        audio, _ = sf.read(audio_filepath)

        # If audio has multiple channels, average them
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        return audio
    except Exception as e:
        print(f"Error@helpers.load_audio :: Failed to read or process the file :: error: {e}, payload: {f"audio_filepath: {audio_filepath}"}")
        return False