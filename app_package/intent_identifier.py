import os
import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from tqdm import tqdm

# Setup device and model
device = "cpu"
torch_dtype = torch.float32
model_id_classification = "tasksource/deberta-small-long-nli"

# Load model and tokenizer for classification
model_classification = AutoModelForSequenceClassification.from_pretrained(
    model_id_classification, torch_dtype=torch_dtype, low_cpu_mem_usage=True
).to(device)
tokenizer_classification = AutoTokenizer.from_pretrained(model_id_classification)

# Create pipelines
pipe_classification = pipeline(
    "zero-shot-classification",
    model=model_classification,
    tokenizer=tokenizer_classification,
    device=device
)

def load_sentences_from_json(file_path):
    """Load sentences from a JSON file and return them as a list."""
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def save_transcription(intent_result, filename, INTENT_DIR):
    """
    Save the transcription text to a file in the TRANSCRIBED_DIR directory.
    """
    os.makedirs(INTENT_DIR, exist_ok=True)
    file_path = os.path.join(INTENT_DIR, filename)

    json_string = json.dumps(intent_result, indent=4)
    try:
        with open(file_path, "w") as file:
            file.write(json_string)
        print(f"Intent file saved to {file_path}")
    except Exception as e:
        print(f"Error saving Intent file: {e}")

def classifier_func(filename, file_path, save_file_path):
    """Classify the intent, sentiment, and emotion of sentences from a JSON file."""
    sentence_list = load_sentences_from_json(file_path)
    keywords = ["Finance"]

    # Initialize progress bar
    pbar = tqdm(total=len(sentence_list), desc="Classifying intent, sentiment, and emotion", unit="sentence")

    results = []

    for sentence_object in sentence_list:
        try:
            # Ensure sentence_object is a dictionary with a 'text' field
            if isinstance(sentence_object, dict) and 'text' in sentence_object:
                # Perform zero-shot classification
                classification = pipe_classification(sentence_object['text'], keywords)
                
                # Enrich the sentence object with classification, sentiment, and emotion
                enriched_sentence = {
                    **sentence_object,
                    'classification': {"label": classification["labels"][0], "score": classification["scores"][0]},
                }
                
                # Append to results
                results.append(enriched_sentence)
                
        except Exception as e:
            print(f"Error processing sentence: {sentence_object}. Error: {e}")

        # Update progress bar
        pbar.update(1)

    # Close progress bar
    pbar.close()
    
    save_transcription(results, filename, save_file_path)

