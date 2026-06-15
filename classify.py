from processor_regex import classify_with_regex
from processor_bert import classify_with_bert
from processor_llm import classify_with_llm
import pandas as pd
import re
import hashlib
from collections import Counter

def generate_log_signature(log_message, source, label):
    """Algorithmic Log Clustering: Strips volatile variables to group identical structures"""
    s = re.sub(r'\b\d{1,3}(?:\.\d{1,3}){3}\b', '<IP>', log_message)
    s = re.sub(r'\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}.*\b', '<TIMESTAMP>', s)
    s = re.sub(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b', '<UUID>', s)
    s = re.sub(r'\b\d+\b', '<NUM>', s)
    sig_str = f"{source}_{label}_{s}"
    return hashlib.md5(sig_str.encode('utf-8')).hexdigest()

def aggregate_results(results_list):
    """Perform Statistical Analysis and format clustered data payload"""
    clusters = {}
    total_logs = len(results_list)
    conf_sum = 0
    conf_count = 0
    source_anomalies = Counter()
    label_counts = Counter()
    
    for res in results_list:
        label = res.get("target_label", "Unclassified")
        source = res.get("source", "Unknown")
        label_counts[label] += 1
        
        # Track anomalous sources (Security Alerts & Errors)
        if label in ["Error", "Security Alert"]:
            source_anomalies[source] += 1
        
        # Calculate numerical confidence for averages
        conf_str = str(res.get("confidence", "0"))
        
        # THE FIX: Safely parse out the number even if there is descriptive text
        if "%" in conf_str:
            # Grabs "100.0%" from "100.0% (Deterministic Match)", then strips "%"
            clean_val = conf_str.split()[0].replace("%", "").strip()
            try:
                conf_sum += float(clean_val)
                conf_count += 1
            except ValueError:
                pass 
        elif "High" in conf_str or "100" in conf_str:
            conf_sum += 100.0
            conf_count += 1
        elif "Automated" in conf_str:
            conf_sum += 90.0
            conf_count += 1
            
        # Cluster matching structures
        sig = generate_log_signature(res["log_message"], source, label)
        if sig not in clusters:
            clusters[sig] = res.copy()
            clusters[sig]["count"] = 1
        else:
            clusters[sig]["count"] += 1
            
    avg_confidence = (conf_sum / conf_count) if conf_count > 0 else 0
    top_anomalies = [{"source": k, "critical_count": v} for k, v in source_anomalies.most_common(3)]
    
    stats = dict(label_counts)
    stats["total"] = total_logs
    stats["avg_confidence"] = f"{avg_confidence:.1f}%"
    stats["anomalies_by_source"] = top_anomalies
    
    return list(clusters.values()), stats

def classify(logs):
    """Classify a list of (source, log_message) tuples"""
    results = []
    for source, log_msg in logs:
        res = classify_log(source, log_msg, verbose=False)
        res["source"] = source
        res["log_message"] = log_msg
        results.append(res)
    return results

def classify_single_log(source, log_message):
    res = classify_log(source, log_message, verbose=False)
    res["source"] = source
    res["log_message"] = log_message
    res["count"] = 1
    return res

def classify_log(source, log_message, verbose=True):
    """Classify a single log message using the hybrid approach and capture XAI metadata"""
    try:
        # 1. Layer 3: LegacyCRM (Special handling for LLM)
        if source == "LegacyCRM":
            llm_res = classify_with_llm(log_message)
            if llm_res:
                return {
                    "target_label": llm_res.get("category", "Unclassified"), 
                    "layer": "Layer 3 (LLM Generative Inference)", 
                    "confidence": "High (Semantic Reasoning)",
                    "reasoning_tokens": llm_res.get("reasoning_tokens", [])
                }
            
            bert_res = classify_with_bert(log_message)
            if bert_res:
                return {
                    "target_label": bert_res["target_label"], 
                    "layer": "Layer 2 (BERT Vector Boundary)", 
                    "confidence": f"{(bert_res['confidence']*100):.1f}%",
                    "reasoning_tokens": bert_res.get("reasoning_tokens", [])
                }

        # 2. Layer 1: Regular Expression (High Precision)
        regex_res = classify_with_regex(log_message)
        if regex_res:
            return {
                "target_label": regex_res["target_label"], 
                "layer": "Layer 1 (Regex Syntactical Rule)", 
                "confidence": "100.0% (Deterministic Match)",
                "reasoning_tokens": regex_res.get("reasoning_tokens", [])
            }
        
        # 3. Layer 2: Sentence Transformer / BERT (High Recall)
        bert_res = classify_with_bert(log_message)
        if bert_res:
            return {
                "target_label": bert_res["target_label"], 
                "layer": "Layer 2 (BERT Vector Boundary)", 
                "confidence": f"{(bert_res['confidence']*100):.1f}%",
                "reasoning_tokens": bert_res.get("reasoning_tokens", [])
            }
        
        # 4. FINAL HEURISTIC FALLBACK
        return {
            "target_label": "System Activity", 
            "layer": "Layer 2 (Heuristic Fallback)", 
            "confidence": "Automated",
            "reasoning_tokens": []
        }
        
    except Exception as e:
        if verbose:
            print(f"[CLASSIFY] Error: {e}")
        return {"target_label": "Unclassified", "layer": "Exception Caught", "confidence": "0%", "reasoning_tokens": []}

def classify_csv(input_file):
    df = pd.read_csv(input_file)
    results = classify(list(zip(df["source"], df["log_message"])))
    clustered, stats = aggregate_results(results)
    
    # Save back unclustered for CLI testing
    df["target_label"] = [r["target_label"] for r in results]
    df["resolving_layer"] = [r["layer"] for r in results]
    df["confidence"] = [r["confidence"] for r in results]
    df.to_csv("resources/output.csv", index=False)
    print(f"Stats: {stats}")

if __name__ == "__main__":
    import os
    os.makedirs("resources", exist_ok=True)
    if os.path.exists("resources/test.csv"):
        classify_csv("resources/test.csv")