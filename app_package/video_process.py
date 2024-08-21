import os
import numpy as np
from PIL import Image, ImageOps
from moviepy.editor import VideoFileClip, ImageSequenceClip
from transformers import DetrForObjectDetection, DetrImageProcessor
import torch
import random

# Load DETR model
processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")

def detect_people(frame):
    """Detect people in a frame using the DETR model."""
    image = Image.fromarray(frame)
    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)
    results = processor.post_process_object_detection(outputs, target_sizes=[image.size[::-1]], threshold=0.9)[0]
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

def zoom_in(image, zoom_factor):
    """Zoom in on an image."""
    width, height = image.size
    new_width = int(width / zoom_factor)
    new_height = int(height / zoom_factor)
    image = image.resize((new_width, new_height), Image.LANCZOS)
    image = ImageOps.fit(image, (width, height), method=0, bleed=0.0, centering=(0.5, 0.5))
    return image

def zoom_out(image, zoom_factor):
    """Zoom out of an image."""
    width, height = image.size
    new_width = int(width * zoom_factor)
    new_height = int(height * zoom_factor)
    image = image.resize((new_width, new_height), Image.LANCZOS)
    image = image.crop(((new_width - width) // 2, (new_height - height) // 2,
                        (new_width + width) // 2, (new_height + height) // 2))
    return image

def crop_frame(frame, focus_box):
    """Crop the frame based on focus box."""
    x_min, y_min, x_max, y_max = focus_box
    cropped = frame[y_min:y_max, x_min:x_max]
    return cropped

def extract_and_process_frames(video_path, frames_dir):
    """Extract and process frames: detect people, apply random zoom effects, resize for TikTok, and save the frame."""
    clip = VideoFileClip(video_path)
    fps = clip.fps
    duration = clip.duration
    frame_count = int(duration * fps)
    
    focus_box = None
    for t in range(frame_count):
        frame = clip.get_frame(t / fps)
        frame = np.array(frame)
        people_boxes = detect_people(frame)
        
        if people_boxes:
            if focus_box is None:
                # Save initial focus box based on the first frame with detected people
                focus_box = get_focus_box(people_boxes, frame.shape)
                cropped_frame = crop_frame(frame, focus_box)
                image = Image.fromarray(cropped_frame)
                # Save the first cropped frame
                initial_frame_path = os.path.join(frames_dir, 'first_cropped_frame.png')
                image.save(initial_frame_path)
            
            cropped_frame = crop_frame(frame, focus_box)
            image = Image.fromarray(cropped_frame)
            
            # zoom_factor = random.uniform(1.1, 2.0) 
            
            # Resize for TikTok aspect ratio
            tiktok_ready_image = resize_for_tiktok(image)
            
            # Save processed frame
            frame_path = os.path.join(frames_dir, f'frame_{t:04d}.png')
            tiktok_ready_image.save(frame_path)
        else:
            # Save original frame if no people are detected
            image = Image.fromarray(frame)
            tiktok_ready_image = resize_for_tiktok(image)
            frame_path = os.path.join(frames_dir, f'frame_{t:04d}.png')
            tiktok_ready_image.save(frame_path)

def create_video_from_frames(output_video_path, frames_dir):
    """Create a video from processed frames, ignoring the first frame."""
    frame_files = sorted(os.listdir(frames_dir))
    
    if len(frame_files) > 0:
        # Exclude the first frame
        frame_files = frame_files[1:]
    
    frames = [os.path.join(frames_dir, file) for file in frame_files]
    
    if frames:
        clip = ImageSequenceClip(frames, fps=30)  # Adjust fps as needed
        clip.write_videofile(output_video_path, codec="libx264")
    else:
        print("No frames available to create the video.")

def crop_video(input_file, output_file, start_time_sec, end_time_sec):
    """Crop video based on time range."""
    clip = VideoFileClip(input_file).subclip(start_time_sec, end_time_sec)
    clip.write_videofile(output_file, codec="libx264")

# Main processing function
def video_process(raw_video_dir, processed_video_dir, filename, reels_script, FRAMES_FOLDER_DIR, PROCESSED_FRAMES_FOLDER_DIR):

    #Crop the raw video according to the start time and end time seconds 

    # input_video = os.path.join(raw_video_dir, filename)
    basename, ext = os.path.splitext(filename)
    cropped_video_filename = basename + '_cropped' + ext
    processed_video_filename = basename + '_processed' + ext
    output_path = os.path.join(processed_video_dir, cropped_video_filename)
    processed_path = os.path.join(processed_video_dir, processed_video_filename)

    # # Crop the video to the specified time range
    # start_time_sec = reels_script['results']['period']['startTime']
    # end_time_sec = reels_script['results']['period']['endTime']
    # crop_video(input_video, output_path, start_time_sec, end_time_sec)

    # in nodejs, 
    # instead of sending the whole script start end and text, 
    # send the results only and include a zoom in duration in certain times so that there is a random duration for zoom in based on high matching of keywords
    # Also figure out a way to add lora text to image generator in the result to generate the image during that time
    # so that the template would be first segments and if longer segments then combined into zoom in and normal view, random insert of zoom out animation image, in the future (maybe movies clips))
    # in the text to image, with the provided segment, figure out a story AI and then feed it to the image generator.

    # Extract and process frames in the frames folder
    # extract_and_process_frames(output_path, FRAMES_FOLDER_DIR)

    #Remove cropped video file 
    #os.remove(output_path)

    # Combine processed frames into a video
    create_video_from_frames(processed_path, PROCESSED_FRAMES_FOLDER_DIR)

    # Clean up temporary frame directory
    # for file in os.listdir(FRAMES_FOLDER_DIR):
    #     os.remove(os.path.join(FRAMES_FOLDER_DIR, file))
    # for file in os.listdir(PROCESSED_FRAMES_FOLDER_DIR):
    #     os.remove(os.path.join(PROCESSED_FRAMES_FOLDER_DIR, file))

    # Extract audio from the video for now but later the audio should already be extracted, just use start_time and end time seconds to crop the audio
    # Get audio files to be transcribed in words 
    # Create substitles based on those words.

    # Combine the audio video and subtitles to create a reel
    
    # Clean up temporary audio, temp video and subtitles directory

    # Based on emotions of the whole segment, add a song to it.

    print(f'Video processed and optimized: {output_path}')