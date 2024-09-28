from moviepy.editor import VideoFileClip, ImageSequenceClip
import numpy as np
from PIL import Image
import os
import math
import subprocess

from app_package.helpers.focus_box import get_focus_box
from models.object_detection_model import object_detection

GLOBAL_FOCUS_BOX = None
FPS = 30
GLOBAL_DOUBLE_FOCUS_BOX = []
DIMENSION = (588, 1046)
TOLERANCE_FACTOR = 0.2

def crop_frame(frame, focus_box, number_of_person):
    cropped = None

    if number_of_person == 1:
        x_min, y_min, x_max, y_max = focus_box[0]
        cropped = frame[y_min:y_max, x_min:x_max]
    
    elif number_of_person == 2:
        global GLOBAL_FOCUS_BOX
        if GLOBAL_FOCUS_BOX:
            # Sort the boxes based on distance to the focus box
            sorted_boxes = sorted(
                focus_box,
                key=lambda box: math.sqrt(
                    ((box[0] + box[2]) / 2 - (GLOBAL_FOCUS_BOX[0] / 2)) ** 2 + 
                    ((box[1] + box[3]) / 2 - (GLOBAL_FOCUS_BOX[1] / 2)) ** 2
                )
            )
        else:
            sorted_boxes = focus_box

        cropped_frames = []
        
        for box in sorted_boxes:
            x_min, y_min, x_max, y_max = box
            new_width = (x_max - x_min) // 2
            new_height = (y_max - y_min) // 2
            
            # Define new maximum coordinates based on half dimensions
            cropped_frame = frame[y_min:y_min + new_height, x_min:x_min + new_width]
            cropped_frames.append(cropped_frame)

        # Stack the cropped frames vertically
        cropped = np.vstack(cropped_frames)

    return cropped

def calculate_tolerance_factor(focus_box):
    global TOLERANCE_FACTOR, GLOBAL_FOCUS_BOX

    # Extract coordinates
    x1_min, y1_min, x1_max, y1_max = focus_box
    x2_min, y2_min, x2_max, y2_max = GLOBAL_FOCUS_BOX
    
    # Calculate width and height for both boxes
    width1 = x1_max - x1_min
    height1 = y1_max - y1_min
    width2 = x2_max - x2_min
    height2 = y2_max - y2_min

    # Calculate allowed tolerance
    width_diff = abs(width1 - width2) / max(width1, width2)
    height_diff = abs(height1 - height2) / max(height1, height2)

    # Check if both width and height differences are within the tolerance
    return width_diff <= TOLERANCE_FACTOR and height_diff <= TOLERANCE_FACTOR

def extract_frames(video_path, frames_processed_path, action):
    global DIMENSION, GLOBAL_FOCUS_BOX, FPS, GLOBAL_DOUBLE_FOCUS_BOX

    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        frame_count = int(duration * FPS)

        # If no directory in cropped video dir for each reels create one 
        os.makedirs(frames_processed_path, exist_ok=True)

        final_verdict_image_ensure = None
        for t in range(frame_count):
            frame = clip.get_frame(t / FPS)
            frame = np.array(frame)
            people_boxes = object_detection(frame, "PEOPLE")

            if len(people_boxes) > 1:
                # More than one person detected
                if GLOBAL_DOUBLE_FOCUS_BOX is None:
                    focus_box_one = get_focus_box([people_boxes[0]], frame.shape)
                    focus_box_two = get_focus_box([people_boxes[1]], frame.shape)
                    GLOBAL_DOUBLE_FOCUS_BOX = [focus_box_one, focus_box_two]

                cropped_frame = crop_frame(frame, GLOBAL_DOUBLE_FOCUS_BOX, 2)
            else:
                # One person detected
                if GLOBAL_FOCUS_BOX is None or not calculate_tolerance_factor(GLOBAL_FOCUS_BOX):
                    GLOBAL_FOCUS_BOX = get_focus_box(people_boxes, frame.shape)

                cropped_frame = crop_frame(frame, [GLOBAL_FOCUS_BOX], 1)

            image = Image.fromarray(cropped_frame)

            tiktok_ready_image = resize_for_reels(image)
            if(action == "ZOOM"):
                zoomed_image = zoom_in_from_sides_except_top(tiktok_ready_image, 1.2)
                final_verdict_image_ensure = ensure_even_dimensions(zoomed_image) #make sure its divisible int
            else:
                final_verdict_image_ensure = ensure_even_dimensions(tiktok_ready_image) #make sure its divisible int
            
            #Filter Dimension requirements
            if not DIMENSION:
                DIMENSION = final_verdict_image_ensure.size
            else:
                final_verdict_image_ensure = final_verdict_image_ensure.resize(DIMENSION, Image.LANCZOS)
        
            frame_path = os.path.join(frames_processed_path, f'frame_{t:04d}.png')
            final_verdict_image_ensure.save(frame_path, format='PNG', quality=100)
        return True
    except Exception as e:
        print(f"Error@blueprint_process.extract_frames :: Error found while cropping video :: error: {e}, payload: {video_path}")
        return False

def combine_frames(reels_processed_directory, frames_processed_path):
    # List and sort frame files
    #Encoding is necessary.
    input_pattern = os.path.join(frames_processed_path, 'frame_%04d.png')
 
    try:
        if input_pattern:
            # Create the FFmpeg command
            command = [
                'ffmpeg',
                '-y',  # Overwrite output file if it exists
                '-framerate', '30',  # Set the frame rate
                '-i', input_pattern,  # Input pattern for the frames
                '-c:v', 'libx264',  # Video codec
                '-crf', '18',
                '-preset', 'veryslow',  # Preset for quality
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                reels_processed_directory,  # Output video file
            ]

            # Execute the command
            subprocess.run(command, check=True)
            return True
        else:
            print(f"Error@blueprint_process.combine_frames :: No freames available to combine :: error: {e}, payload: {reels_processed_directory}")
            return False
    except Exception as e:
        print(f"Error@blueprint_process.combine_frames :: Error found while combining frames :: error: {e}, payload: {reels_processed_directory}")
        raise False
    finally:
        # Delete frames_processed_path
        os.remove(frames_processed_path)

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

def resize_for_reels(image):
    """Resize or crop the image to fit Reels's 9:16 aspect ratio."""
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

def ensure_even_dimensions(image):
    width, height = image.size
    # Adjust dimensions to be divisible by 2
    if width % 2 != 0:
        width -= 1
    if height % 2 != 0:
        height -= 1
    return image.resize((width, height)).convert('RGB')