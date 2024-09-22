from PIL import Image
from transformers import DetrForObjectDetection, DetrImageProcessor
import torch

# Load DETR model and processor once
processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50").eval()

# Check for GPU availability
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def object_detection(frame, object_type):
    try:
        if object_type == "PEOPLE":
            label_type = 1
        with torch.no_grad():  # Disable gradient calculation for inference
            image = Image.fromarray(frame).convert("RGB")  # Ensure image is in RGB format
            inputs = processor(images=image, return_tensors="pt").to(device)
            outputs = model(**inputs)
            results = processor.post_process_object_detection(
                outputs,
                target_sizes=[image.size[::-1]],
                threshold=0.9
            )[0]

            # Extract bounding boxes for people (label = 1)
            people_boxes = [
                box for label, box in zip(results["labels"], results["boxes"]) if label == label_type
            ]
        return people_boxes

    except Exception as e:
        print(f"Error@models.object_detection :: Error during Detecting Objects :: error: {e}")
        return False