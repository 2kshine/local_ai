import os
import soundfile as sf
from scipy.signal import resample
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import torch
import numpy as np
from tqdm import tqdm
import json
import whisper_timestamped

device = "cpu"
torch_dtype = torch.float32

model_id = "openai/whisper-small"

# Initialize model and processor
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
).to(device)


processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    max_new_tokens=128,
    chunk_length_s=25,
    batch_size=16,
    torch_dtype=torch_dtype,
    device=device,
)

def resample_audio(audio, original_sr, target_sr=16000):
    """
    Resample audio to the target sampling rate using scipy.
    """
    number_of_samples = round(len(audio) * float(target_sr) / original_sr)
    if number_of_samples <= 0:
        raise ValueError("Number of samples for resampling is non-positive.")
    return resample(audio, number_of_samples)


def load_audio(file_path):
    """
    Load and return audio data and its sampling rate from a local audio file.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file at path {file_path} does not exist.")
    
    try:
        audio, sampling_rate = sf.read(file_path)
        if len(audio.shape) > 1 and audio.shape[1] > 1:
            audio = np.mean(audio, axis=1)
        if sampling_rate != 16000:
            audio = resample_audio(audio, sampling_rate)
    except Exception as e:
        raise ValueError(f"Failed to read or process the file: {e}")

    return {"audioFile": audio, "original_sampling_rate": sampling_rate}


def transcribe_audio(audio_data, filename, TRANSCRIBED_DIR, RAW_TRANSCRIBED_DIR):
    """
    Transcribe the given audio data using the pipeline.
    """
    with torch.no_grad():
        pbar = tqdm(total=1, desc="Transcribing", unit="step")
        transcription = pipe(audio_data["audioFile"], return_timestamps=True)
        pbar.update(1)
        pbar.close()
    #Change file extensions for both transcribed and raw transcribed.
    basename, _ = os.path.splitext(filename)
    filename_chunk = basename + ".json"
    filename_text = basename + ".txt"
    save_transcription(transcription["chunks"], transcription["text"], filename_chunk, filename_text, TRANSCRIBED_DIR, RAW_TRANSCRIBED_DIR)

def save_transcription(transcription_chunk, transcription_text, filename_chunk, filename_text, TRANSCRIBED_DIR, RAW_TRANSCRIBED_DIR):
    """
    Save the transcription text to a file in the TRANSCRIBED_DIR directory.
    """
    os.makedirs(TRANSCRIBED_DIR, exist_ok=True)
    os.makedirs(RAW_TRANSCRIBED_DIR, exist_ok=True)
    file_path_chunk = os.path.join(TRANSCRIBED_DIR, filename_chunk)
    file_path_text = os.path.join(RAW_TRANSCRIBED_DIR, filename_text)

    json_output = [
        {
            "start": chunk["timestamp"][0],
            "end": chunk["timestamp"][1],
            "text": chunk["text"].strip(),
        }
        for chunk in transcription_chunk
    ]

    json_string = json.dumps(json_output, indent=4)
    try:
        with open(file_path_chunk, "w") as file:
            file.write(json_string)

        # Open the file in write mode and write the string to it
        with open(file_path_text, 'w') as file:
            file.write(transcription_text)
        print(f"Transcription saved to {file_path_chunk} and {file_path_text}")
    except Exception as e:
        print(f"Error saving transcription: {e}")

def extract_words(audioFilePath, filename_words):
    model = whisper_timestamped.load_model("small.en", device="cpu")
    with torch.no_grad():
        pbar = tqdm(total=1, desc="Transcribing", unit="step", dynamic_ncols=True)
        audio = whisper_timestamped.load_audio(audioFilePath)
        transcribedWords = whisper_timestamped.transcribe(model, audio, language="en")
        print(transcribedWords)
        pbar.update(1)  # Update progress bar
        pbar.close()  # Close progress bar
    #Change file extensions for both transcribed and raw transcribed.
    try:
        extracted_data = []
        for segment in transcribedWords['segments']:
            for word in segment['words']:
                extracted_data.append({
                    'text': word['text'],
                    'start': word['start'],
                    'end': word['end']
                })
        
        # Convert list to JSON-formatted string
        json_data = json.dumps(extracted_data, indent=4)

        # Open the file in write mode and write the string to it
        with open(filename_words, 'w') as file:
            file.write(json_data)
        print(f"Words extracted, saved to {filename_words}")
    except Exception as e:
        print(f"Error saving transcription: {e}")

