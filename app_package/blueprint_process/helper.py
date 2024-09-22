from moviepy.editor import VideoFileClip, ImageSequenceClip
import numpy as np
from PIL import Image
import os

from app_package.helpers.focus_box import get_focus_box
from models.object_detection_model import object_detection

GLOBAL_FOCUS_BOX = None
FPS = 30
DIMENSION = (588, 1046)
def crop_frame(frame, focus_box):
    x_min, y_min, x_max, y_max = focus_box
    cropped = frame[y_min:y_max, x_min:x_max]
    return cropped

def extract_frames(video_path, frames_processed_path, action):
    global DIMENSION, GLOBAL_FOCUS_BOX, FPS

    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        frame_count = int(duration * FPS)

        # If no directory in cropped video dir for each reels create one 
        if not os.path.exists(frames_processed_path):
            os.makedirs(frames_processed_path)

        frame_path = os.path.join(frames_processed_path, f'frame_{t:04d}.png')
        final_verdict_image_ensure = None
        for t in range(frame_count):
            frame = clip.get_frame(t / FPS)
            frame = np.array(frame)
            people_boxes = object_detection(frame, "PEOPLE")

            if len(people_boxes) == 1:
                # One person is detected
                if GLOBAL_FOCUS_BOX is None:
                    focus_box = get_focus_box(people_boxes, frame.shape)
                    cropped_frame = crop_frame(frame, focus_box)
                    image = Image.fromarray(cropped_frame)
                    GLOBAL_FOCUS_BOX = focus_box
                else:
                    focus_box = GLOBAL_FOCUS_BOX
                cropped_frame = crop_frame(frame, focus_box)
                image = Image.fromarray(cropped_frame)

                if(action == "ZOOM"):
                    tiktok_ready_image = resize_for_reels(image)
                    zoomed_image = zoom_in_from_sides_except_top(tiktok_ready_image, 1.2)
                    final_verdict_image_ensure = ensure_even_dimensions(zoomed_image) #make sure its divisible int
                else:
                    tiktok_ready_image = resize_for_reels(image)
                    final_verdict_image_ensure = ensure_even_dimensions(tiktok_ready_image) #make sure its divisible int
            
            elif len(people_boxes) > 1:
                # More than one person id detected
                print('Not yet configured')
            
            else:
                # No people is detected.
                # Detect a random object and crop around it.
                print("No detection") 

            #Filter Dimension requirements
            if not DIMENSION:
                DIMENSION = final_verdict_image_ensure.size
            else:
                final_verdict_image_ensure = final_verdict_image_ensure.resize(DIMENSION, Image.LANCZOS)
         
            final_verdict_image_ensure.save(frame_path, format='PNG', quality=100)
        return True
    except Exception as e:
        print(f"Error@blueprint_process.extract_frames :: Error found while cropping video :: error: {e}, payload: {video_path}")
        return False

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