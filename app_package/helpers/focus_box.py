def get_focus_box(boxes, frame_shape):
    """Get bounding box around the detected object"""
    if not boxes:
        return (0, 0, frame_shape[1], frame_shape[0])
    x_min = min(box[0] for box in boxes)
    y_min = min(box[1] for box in boxes)
    x_max = max(box[2] for box in boxes)
    y_max = max(box[3] for box in boxes)
    return (int(x_min), int(y_min), int(x_max), int(y_max))