
from PIL import Image
from transformers import DetrForObjectDetection, DetrImageProcessor
import subprocess
import json
from moviepy.editor import VideoFileClip
import os 
from app_package.helpers.directory_helper import TEMPORARY_ACTIONS


# Load DETR model
processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")

def detect_people(frame):
    """Detect people in a frame using the DETR model."""
    image = Image.fromarray(frame)
    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)
    results = processor.post_process_object_detection(outputs, target_sizes=[image.size[::-1]], threshold=0.9)[0] # 0.9 to include only 90% accuracy
    people_boxes = [box for label, box in zip(results["labels"], results["boxes"]) if label == 1]
    return people_boxes

def get_focus_box(boxes, frame_shape):
    """Get bounding box around all detected people."""
    if not boxes:
        return (0, 0, frame_shape[1], frame_shape[0])
    x_min = min(box[0] for box in boxes)
    y_min = min(box[1] for box in boxes)
    x_max = max(box[2] for box in boxes)
    y_max = max(box[3] for box in boxes)
    return (int(x_min), int(y_min), int(x_max), int(y_max))

def resize_for_tiktok(image):
    """Resize or crop the image to fit TikTok's 9:16 aspect ratio."""
    width, height = image.size
    target_aspect_ratio = 9 / 16

    if width / height > target_aspect_ratio:
        # Width is too large, crop the sides
        new_width = int(height * target_aspect_ratio)
        left = (width - new_width) // 2
        right = left + new_width
        image = image.crop((left, 0, right, height))
    elif width / height < target_aspect_ratio:
        # Height is too large, crop the top and bottom
        new_height = int(width / target_aspect_ratio)
        top = (height - new_height) // 2
        bottom = top + new_height
        image = image.crop((0, top, width, bottom))

    return image

def zoom_in_from_sides_except_top(img, zoom_factor):
    # Open the image
    original_width, original_height = img.size

    # Calculate new dimensions
    new_width = int(original_width * zoom_factor)
    new_height = int(original_height * zoom_factor)

    # Resize the image
    resized_img = img.resize((new_width, new_height), Image.LANCZOS)

    # Calculate cropping box to crop from the top and sides
    left = (new_width - original_width) // 2
    top = 0
    right = left + original_width
    bottom = original_height

    # Crop the image
    cropped_img = resized_img.crop((left, top, right, bottom))

    return cropped_img

def crop_frame(frame, focus_box):
    """Crop the frame based on focus box."""
    x_min, y_min, x_max, y_max = focus_box
    cropped = frame[y_min:y_max, x_min:x_max]
    return cropped

def ensure_even_dimensions(image):
    width, height = image.size
    # Adjust dimensions to be divisible by 2
    if width % 2 != 0:
        width -= 1
    if height % 2 != 0:
        height -= 1
    return image.resize((width, height)).convert('RGB')

def get_video_bitrate(file_path):
    # Run ffprobe to get video information
    command = [
        'ffprobe', 
        '-v', 'error', 
        '-select_streams', 'v:0', 
        '-show_entries', 'stream=bit_rate', 
        '-of', 'json',
        file_path
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    data = json.loads(result.stdout)
    
    if 'streams' in data and len(data['streams']) > 0:
        bitrate = data['streams'][0].get('bit_rate')
        if bitrate:
            # Convert bitrate to kilobits per second (kbps)
            return int(bitrate) // 1000
    return None

def crop_video(input_file, output_file, start_time_sec, end_time_sec):
    try:
        # Get the original bitrate
        original_bitrate = get_video_bitrate(input_file)
        if original_bitrate is None:
            raise ValueError("Could not determine the original bitrate.")
        
        # Set a high bitrate for HD quality
        # Typical bitrates for HD quality: 720p ~ 5 Mbps, 1080p ~ 10 Mbps
        target_bitrate = '10000k'  # 10 Mbps for 1080p HD
        bufsize = f"{2 * int(target_bitrate[:-1])}k"  # Dynamic buffer size
        
        # Load the video clip
        clip = VideoFileClip(input_file)
        
        # Crop the clip based on the specified time range
        cropped_clip = clip.subclip(start_time_sec, end_time_sec)
        
        # Ensure the output resolution is HD (if necessary)
        # This ensures the output resolution is at least 1080p
        width, height = cropped_clip.size
        if width < 1920 or height < 1080:
            cropped_clip = cropped_clip.resize(newsize=(1920, 1080))

        # Set the desired frame rate
        fps = 30

        # Write the cropped clip to the output file with HD quality settings
        cropped_clip.write_videofile(
            output_file, 
            codec='libx264',
            fps=fps,  # Set frame rate to 30 fps
            preset='veryslow',  # Use 'veryslow' for better quality
            ffmpeg_params=[
                '-profile:v', 'high',
                '-b:v', target_bitrate,  # Set the bitrate for HD quality
                '-maxrate', target_bitrate,
                '-bufsize', bufsize  # Dynamic buffer size
            ],
        )
        
        # Close the clips to release resources
        clip.close()
        cropped_clip.close()

        print(f"Video cropped and saved to '{output_file}'.")
    except Exception as e:
        print(f"Error found while cropping video from input_file {input_file}: {e}")
        raise e
    
def add_silence(video_path, output_path, duration):
    try:
        # Generate a silent audio track with the same duration as the video
        silence_audio = os.path.join(TEMPORARY_ACTIONS, 'silence.mp3')
        command = [
            'ffmpeg', '-f', 'lavfi', '-t', str(duration), '-i', 'anullsrc=r=48000:cl=stereo', '-q:a', '9', '-acodec', 'libmp3lame', silence_audio
        ]
        subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Combine video with silent audio
        command = [
            'ffmpeg', '-i', video_path, '-i', silence_audio, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', output_path
        ]
        subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error adding silence: {e.stderr}")
    finally:
        # Clean up the temporary silence file
        if os.path.exists(silence_audio):
            os.remove(silence_audio)

