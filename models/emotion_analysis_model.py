from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch

# Setup device and model
device = "cpu"
torch_dtype = torch.float32
model_id_sentiment = "avichr/heBERT_sentiment_analysis"
model_id_emotion = "SamLowe/roberta-base-go_emotions"

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

def emotion_analysis(segment):
    sentiments = []
    emotions = []
    
    try:
        with torch.no_grad():  # Disable gradient calculation for inference
            # Perform sentiment analysis
            sentiments = pipe_sentiment(segment)

            # Perform emotion analysis
            emotions = pipe_emotion(segment)

            print(f"Success@models.emotion_analysis :: Success on emotion analysis :: payload: {segment}")
            return {'sentiments': sentiments[0], 'emotions': emotions[0]}    
    except Exception as e:
        print(f"Error@models.emotion_analysis :: Error processing sentence :: error: {e}, payload: {segment}")
        return False
    
    