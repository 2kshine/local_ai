import imageio
import numpy as np
from PIL import Image
import os

from app_package.helpers.focus_box import get_focus_box
from app_package.helpers.directory_helper import PROCESSED_VIDEO_DIR
from app_package.animate_image.helper import zoom_in, zoom_out
from models.object_detection_model import object_detection

def link_to_reels_action_animate_image(basename, image_filepath, dimension, animation_duration, fps, logging_object):
    #Process image, check if any peoples are detected, if detected zoom in else out
    image = Image.open(image_filepath)
    image = image.resize(dimension).convert('RGB')
    single_frame = np.array(image)
    people_boxes = object_detection(single_frame, "PEOPLE")
    zoom_center = (image.width // 2, image.height // 2)     

    #File Path to save to 
    unique_directory_name = os.path.join(PROCESSED_VIDEO_DIR, "_".join(basename.split("_")[:2]))
    save_file_path = os.path.join(unique_directory_name, f"{basename}.avi")
    if people_boxes:
        zoom_vertices = get_focus_box(people_boxes, single_frame.shape)
        if not zoom_out(image, save_file_path, animation_duration, zoom_vertices, fps, logging_object):
            return False
    else:
        if not zoom_in(image, save_file_path, animation_duration, zoom_center, fps, logging_object):
            return False