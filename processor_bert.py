import joblib
from sentence_transformers import SentenceTransformer
import os
import re

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

def extract_attention_tokens(model_embedding, model_classification, message, base_prob, predicted_label):
    """Simulates XAI attention extraction via rapid feature ablation."""
    words = re.findall(r'\b\w+\b', message)
    if len(words) > 15: # Cap to prevent performance hits
        words = words[:15]
        
    classes = list(model_classification.classes_)
    if predicted_label not in classes:
        return []
    
    pred_idx = classes.index(predicted_label)
    impact_scores = []
    
    for i, word in enumerate(words):
        if len(word) < 4: continue
        # Mask the word and measure confidence drop
        masked_msg = " ".join(words[:i] + words[i+1:])
        emb = model_embedding.encode([masked_msg])
        prob = model_classification.predict_proba(emb)[0][pred_idx]
        drop = base_prob - prob
        
        if drop > 0.01: # Meaningful drop in confidence
            impact_scores.append((word, drop))
            
    # Sort by highest impact and return top 2
    impact_scores.sort(key=lambda x: x[1], reverse=True)
    return [word for word, score in impact_scores[:2]]

def classify_with_bert(log_message):
    """Classify logs using BERT embeddings and logistic regression"""
    try:
        model_embedding, model_classification = _load_models()
        
        if model_classification is None or model_embedding is None:
            return None
        
        # 1. Map to Vector Space
        embeddings = model_embedding.encode([log_message])
        
        # 2. Predict using Logistic Regression
        predicted_label = model_classification.predict(embeddings)[0]
        
        # 3. Calculate Confidence Score
        probabilities = model_classification.predict_proba(embeddings)[0]
        max_prob = float(max(probabilities))
        
        if max_prob < 0.3:
            return None
            
        # 4. Extract Reasoning Tokens (XAI)
        tokens = extract_attention_tokens(model_embedding, model_classification, log_message, max_prob, predicted_label)
        
        return {
            "target_label": predicted_label,
            "confidence": max_prob,
            "reasoning_tokens": tokens
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None