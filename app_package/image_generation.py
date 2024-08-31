from transformers import pipeline
import imageio
import numpy as np
from PIL import Image
from app_package.helpers import (
    detect_people,
    get_focus_box
)

ZOOM_FACTOR=1.4
FPS=30
# def crop_frame(frame, focus_box):
#     """Crop the frame based on focus box."""
#     x_min, y_min, x_max, y_max = focus_box
#     cropped = frame[y_min:y_max, x_min:x_max]
#     return cropped

def animate_image(image_filepath, saveFilePath, duration, dimension):
    #Process image, check if any peoples are detected, if detected zoom in else out
    image = Image.open(image_filepath)
    image = image.resize(dimension).convert('RGB')
    single_frame = np.array(image)
    people_boxes = detect_people(single_frame)
    zoom_center = (image.width // 2, image.height // 2)     
    if people_boxes:
        zoom_vertices = get_focus_box(people_boxes, single_frame.shape)
        zoom_out(image, saveFilePath, duration, zoom_vertices)
    else:
        zoom_in(image, saveFilePath, duration, zoom_center)

def zoom_in(image, saveFilePath, duration, zoom_center):
    width, height = image.size
    frames = []

    total_frames = int(FPS * duration)

    # Add zoom-in animation
    for i in range(total_frames):
        scale = 1 + i * (ZOOM_FACTOR - 1) / (total_frames - 1)
        new_width = int(width / scale)
        new_height = int(height / scale)
        
        # Calculate crop box coordinates
        left = int(zoom_center[0] - new_width // 2)
        upper = int(zoom_center[1] - new_height // 2)
        right = int(zoom_center[0] + new_width // 2)
        lower = int(zoom_center[1] + new_height // 2)
        
        # Ensure coordinates are within image bounds
        left, upper = max(0, left), max(0, upper)
        right, lower = min(width, right), min(height, lower)
        
        # Crop and resize the image
        cropped_image = image.crop((left, upper, right, lower))
        resized_image = cropped_image.resize((width, height), Image.LANCZOS)
        
        # Convert to numpy array and add to frames list
        frame = np.array(resized_image)
        frames.append(frame)
    
    # Save as video
    with imageio.get_writer(saveFilePath, fps=FPS, macro_block_size=1, codec='libx264') as writer:
        for frame in frames:
            writer.append_data(frame)

def zoom_out(image, saveFilePath, duration, zoom_vertices):
    global ZOOM_FACTOR, FPS
    width, height = image.size

    frames = []

    total_frames = round(FPS * duration)  # Total number of frames

    # Calculate the initial bounding box size
    left, upper, right, lower = zoom_vertices
    box_width = right - left
    box_height = lower - upper

    # Calculate the maximum zoom factor needed to fit the whole image
    zoom_factor_width = width / box_width
    zoom_factor_height = height / box_height
    initial_zoom_factor = max(zoom_factor_width, zoom_factor_height)

    # Add zoom-out animation
    for i in range(total_frames):
        # Scale decreases from initial_zoom_factor to 1
        scale = initial_zoom_factor - (i / total_frames) * (initial_zoom_factor - 1)

        # Calculate crop box coordinates based on current scale
        crop_left = left - (width / scale - box_width) / 2
        crop_upper = upper - (height / scale - box_height) / 2
        crop_right = left + (width / scale + box_width) / 2
        crop_lower = upper + (height / scale + box_height) / 2

        # Ensure coordinates are within image bounds
        crop_left, crop_upper = max(0, crop_left), max(0, crop_upper)
        crop_right, crop_lower = min(width, crop_right), min(height, crop_lower)

        # Crop and resize the image
        cropped_image = image.crop((crop_left, crop_upper, crop_right, crop_lower))
        resized_image = cropped_image.resize((width, height), Image.LANCZOS)
        
        frame = np.array(resized_image)
        frames.append(frame)

    # Save as video
    with imageio.get_writer(saveFilePath, fps=FPS, macro_block_size=1, codec='libx264') as writer:
        for frame in frames:
            writer.append_data(frame)