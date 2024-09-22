import subprocess

def crop_video(input_file, output_file, start_time_sec, end_time_sec):
    logging_object = {
        'input_file': input_file,
        'output_file': output_file,
        'start_time_sec': start_time_sec,
        'end_time_sec': end_time_sec
    }
    try:
        # Construct the FFmpeg command
        command = [
            'ffmpeg',
            '-i', input_file,
            '-ss', str(start_time_sec),
            '-to', str(end_time_sec),
            '-c:v', 'copy',                 # Copy video stream without re-encoding
            '-c:a', 'copy',                 # Copy audio stream without re-encoding
            '-y',
            output_file
        ]
        
        # Run the FFmpeg command
        subprocess.run(command, check=True)

        print(f"Success@helpers.crop_video :: Success on cropping video :: payload: {logging_object}")
        return True
    except Exception as e:
        print(f"Error@helpers.crop_video :: Error cropping the video :: error: {e}, payload: {logging_object}")
        return False