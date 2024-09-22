import whisper_timestamped
from tqdm import tqdm
import torch

#Initialize the model
model = whisper_timestamped.load_model("small.en", device="cpu")

def transcribe_audio(audio_filepath):
    try:
        transcribed_result = None

        #Setup the loading plus run the model.
        with torch.no_grad():
            pbar = tqdm(total=1, desc=f"Transcribing audio file {audio_filepath}", unit="step", dynamic_ncols=True)
            audio = whisper_timestamped.load_audio(audio_filepath)
            if not audio:
                print(f"Error@models.transcribe_audio :: Error found while loading audio for the file :: payload: {f"audio_filepath: {audio_filepath}"}")
                return False
            transcribed_result = whisper_timestamped.transcribe(model, audio, language="en")
            pbar.update(1)  # Update progress bar
            pbar.close()  # Close progress bar

        return transcribed_result 

    except Exception as e:
        print(f"Error@models.transcribe_audio :: Error found while transcribing audio for the file :: error: {e}, payload: {f"audio_filepath: {audio_filepath}"}")
        return False
    
    finally:
        pbar.close()  # Ensure the progress bar closes