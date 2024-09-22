import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

def setup_device_and_model(model_id):
    # Load model and tokenizer for classification
    model = AutoModelForSequenceClassification.from_pretrained(
        model_id, torch_dtype=torch.float32, low_cpu_mem_usage=True
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    return model, tokenizer

# Setup device and load model
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id_classification = "tasksource/deberta-small-long-nli"
model_classification, tokenizer_classification = setup_device_and_model(model_id_classification)

# Move model to device
model_classification.to(device)

# Create pipelines
intent_classification = pipeline(
    "zero-shot-classification",
    model=model_classification,
    tokenizer=tokenizer_classification,
    device=0 if torch.cuda.is_available() else -1  # Use GPU if available
)

def intent_identify(sentence, keywords):
    try:
        with torch.no_grad():  # Disable gradient calculation for inference
            result = intent_classification(sentence, keywords)
        return result  # Directly return the result

    except Exception as e:
        print(f"Error@models.intent_identify :: Error during intent identify :: error: {e}, payload: {f"sentence: {sentence}, keywords:{keywords}"}")
        return False