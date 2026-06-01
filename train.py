import os
import random
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib


# -----------------------------
# 1. SYNTHETIC DATA GENERATOR
# -----------------------------
def generate_samples(label, templates, n=100):
    samples = []
    for _ in range(n):
        template = random.choice(templates)
        samples.append((template, label))
    return samples


def build_dataset():
    random.seed(42)

    data = []

    # ---------------- NETWORK ANOMALY ----------------
    network_templates = [
        "Packet loss detected in {} segment.",
        "High latency observed in {} service.",
        "Connection timeout from {} node.",
        "Gateway failure in {} region.",
        "DNS resolution failure for {} service.",
        "Load balancer health check failed for {}.",
        "Network jitter exceeding threshold in {}.",
        "Service unreachable due to {} routing issue."
    ]

    data += generate_samples("Network Anomaly", network_templates, 100)

    # ---------------- RESOURCE WARNING ----------------
    resource_templates = [
        "CPU usage at {}% for extended period.",
        "Memory usage critically high in {} process.",
        "Disk space below {}% threshold.",
        "GPU utilization maxed out on {} node.",
        "Swap memory exhaustion detected in {} system.",
        "Container {} exceeded memory limit.",
        "High load average on {} server.",
        "Thread exhaustion detected in {} service."
    ]

    data += generate_samples("Resource Warning", resource_templates, 100)

    # ---------------- DATABASE ERROR ----------------
    db_templates = [
        "Database connection timeout in {}.",
        "Deadlock detected in {} transaction.",
        "SQL syntax error in {} query.",
        "Primary database {} is unreachable.",
        "Index corruption detected in {} table.",
        "Transaction rollback in {} due to constraint violation.",
        "Replica node failure in {} cluster.",
        "Query execution timeout in {} database."
    ]

    data += generate_samples("Database Error", db_templates, 100)

    # ---------------- CRITICAL EXCEPTION ----------------
    critical_templates = [
        "System crash due to {} exception.",
        "Fatal error in {} module.",
        "Unhandled exception in {} service.",
        "Kernel panic triggered on {} node.",
        "Segmentation fault in {} process.",
        "Application terminated unexpectedly in {}.",
        "Runtime crash in {} execution engine.",
        "Core dump generated in {} system."
    ]

    data += generate_samples("Critical Exception", critical_templates, 100)

    # ---------------- SECURITY ALERT ----------------
    security_templates = [
        "Unauthorized access attempt detected from {} IP.",
        "Brute force attack blocked on {}.",
        "Malware detected in {} upload.",
        "SQL injection attempt blocked in {}.",
        "Suspicious login detected from {} device.",
        "Firewall blocked traffic from {}.",
        "Privilege escalation attempt in {} system.",
        "Data exfiltration attempt from {} endpoint."
    ]

    data += generate_samples("Security Alert", security_templates, 100)

    return data


# -----------------------------
# 2. TRAINING PIPELINE
# -----------------------------
def train_model():
    print("Generating dataset...")
    training_data = build_dataset()

    df = pd.DataFrame(training_data, columns=["log_message", "label"])
    print(f"Total samples: {len(df)}")
    print(df["label"].value_counts())

    print("Loading embedding model...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    print("Encoding text...")
    X = embedder.encode(df["log_message"].tolist(), convert_to_numpy=True)
    y = df["label"].tolist()

    # -----------------------------
    # TRAIN / TEST SPLIT
    # -----------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print("Training Logistic Regression...")
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_train, y_train)

    # -----------------------------
    # EVALUATION
    # -----------------------------
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"Test Accuracy: {acc * 100:.2f}%")

    # -----------------------------
    # SAVE MODELS
    # -----------------------------
    os.makedirs("models", exist_ok=True)

    joblib.dump(model, "models/log_classifier.joblib")
    joblib.dump(embedder, "models/embedder.joblib")

    print("Model saved successfully.")


if __name__ == "__main__":
    train_model()