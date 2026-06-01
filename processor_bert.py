import joblib
from sentence_transformers import SentenceTransformer
import os

# Defer loading until first use
_model_embedding = None
_model_classification = None
_models_loaded = False

def _load_models():
    global _model_embedding, _model_classification, _models_loaded
    
    if _models_loaded:
        return _model_embedding, _model_classification
    
    try:
        print("[BERT] Loading Sentence Transformer model...")
        _model_embedding = SentenceTransformer('all-MiniLM-L6-v2')
        print("[BERT] ✓ Embedding model loaded")
    except Exception as e:
        print(f"[BERT] ✗ Error loading embedding model: {e}")
        _model_embedding = None
    
    try:
        model_path = "models/log_classifier.joblib"
        if os.path.exists(model_path):
            print(f"[BERT] Loading classifier model from {model_path}...")
            _model_classification = joblib.load(model_path)
            print("[BERT] ✓ Classifier model loaded")
        else:
            print(f"[BERT] ✗ Model file not found at {model_path}")
            _model_classification = None
    except Exception as e:
        print(f"[BERT] ✗ Error loading classifier model: {e}")
        _model_classification = None
    
    _models_loaded = True
    return _model_embedding, _model_classification

def classify_with_bert(log_message):
    """Classify logs using BERT embeddings and logistic regression"""
    try:
        print(f"[BERT] Classifying: {log_message[:60]}...")
        model_embedding, model_classification = _load_models()
        
        if model_classification is None or model_embedding is None:
            print("[BERT] ✗ ML Models not available. Run train.py first.")
            return None, 0.0
        
        # 1. Map to Vector Space
        print("[BERT] Encoding message...")
        embeddings = model_embedding.encode([log_message])
        
        # 2. Predict using Logistic Regression
        print("[BERT] Predicting...")
        predicted_label = model_classification.predict(embeddings)[0]
        
        # 3. Calculate Confidence Score
        probabilities = model_classification.predict_proba(embeddings)[0]
        max_prob = float(max(probabilities))
        
        classes = model_classification.classes_
        print(f"[BERT] Probabilities: {dict(zip(classes, probabilities))}")
        print(f"[BERT] Confidence: {max_prob:.2%} ({predicted_label})")
        
        # Threshold set to 0.5 (50%) for reliable predictions
        # If confidence is lower, we reject it so Layer 3 (LLM) can take over
        if max_prob < 0.3:
            print(f"[BERT] ✗ Confidence too low ({max_prob:.2%})")
            return None, 0.0
        
        print(f"[BERT] ✓ Predicted: {predicted_label}")
        return predicted_label, max_prob
        
    except Exception as e:
        print(f"[BERT] ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, 0.0