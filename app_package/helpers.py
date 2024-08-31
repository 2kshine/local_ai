
from PIL import Image, ImageOps
from transformers import DetrForObjectDetection, DetrImageProcessor

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
