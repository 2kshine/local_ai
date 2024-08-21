from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from tqdm import tqdm

# Setup device and model
device = "cpu"
torch_dtype = torch.float32
model_id_sentiment = "avichr/heBERT_sentiment_analysis"
model_id_emotion = "michellejieli/emotion_text_classifier"

# Load model and tokenizer for sentiment analysis
model_sentiment = AutoModelForSequenceClassification.from_pretrained(
    model_id_sentiment, torch_dtype=torch_dtype, low_cpu_mem_usage=True
).to(device)
tokenizer_sentiment = AutoTokenizer.from_pretrained(model_id_sentiment)

# Load model and tokenizer for emotion analysis
model_emotion = AutoModelForSequenceClassification.from_pretrained(
    model_id_emotion, torch_dtype=torch_dtype, low_cpu_mem_usage=True
).to(device)
tokenizer_emotion = AutoTokenizer.from_pretrained(model_id_emotion)

pipe_sentiment = pipeline(
    "sentiment-analysis",
    model=model_sentiment,
    tokenizer=tokenizer_sentiment,
    device=device
)

pipe_emotion = pipeline(
    "sentiment-analysis",
    model=model_emotion,
    tokenizer=tokenizer_emotion,
    device=device
)

def emotion_func(segment):
    # Initialize progress bar
    pbar = tqdm(total=len(segment), desc="Classifying sentiment and emotion", unit="sentence")
    
    sentiments = []
    emotions = []
    
    try:
        # Perform sentiment analysis
        sentiments = pipe_sentiment(segment)

        # Perform emotion analysis
        emotions = pipe_emotion(segment)
            
    except Exception as e:
        print(f"Error processing sentence. Error: {e}")
    finally:
        # Update progress bar
        pbar.update(1)
        # Close progress bar
        pbar.close()
    
    return {'sentiments': sentiments[0], 'emotions': emotions[0]}