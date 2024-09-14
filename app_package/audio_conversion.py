import os
import subprocess
import soundfile as sf

def convert_audio(file_path, output_format='wav'):
    """
    Convert audio file to the specified format using ffmpeg.

    Args:
        file_path (str): Path to the original audio file.
        output_format (str): Desired output format (default is 'wav').

    Returns:
        str: Path to the converted audio file.
    """
    base, _ = os.path.splitext(file_path)
    converted_file_path = f"{base}.{output_format}"
    
    # Run ffmpeg command to convert the audio file
    try:
        subprocess.run([
            'ffmpeg', '-i', file_path,
            '-f', output_format,
            converted_file_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"An error occurred during conversion: {e.stderr.decode()}")

    return converted_file_path

def load_audio(file_path):
    """
    Load and return audio data and its sampling rate from a local audio file.

    Args:
        file_path (str): Path to the audio file.

    Returns:
        dict: A dictionary containing:
            - "array": Audio data as a NumPy array.
            - "sampling_rate": The sampling rate of the audio file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported and cannot be converted.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file at path {file_path} does not exist.")
    
    supported_formats = ('.wav', '.flac', '.ogg')
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension not in supported_formats:
        if file_extension == '.mp4':  # Example of unsupported formats
            # Convert to WAV if the format is not supported
            converted_file_path = convert_audio(file_path, 'wav')
            file_path = converted_file_path
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Attempting conversion.")
    
    try:
        audio, sampling_rate = sf.read(file_path)
    except Exception as e:
        raise RuntimeError(f"An error occurred while reading the audio file: {e}")

    return {"array": audio, "sampling_rate": sampling_rate}

def main():
    # Path to local audio file
    audio_file_path = 'videoplayback.m4a'  # Update this path to your audio file

    try:
        # Load audio file
        audio_sample = load_audio(audio_file_path)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()