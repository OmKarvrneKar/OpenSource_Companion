"""
train_classifier.py
Run once to train the XGBoost + TF-IDF difficulty classifier.
Saves: models/classifier.pkl, models/tfidf_vectorizer.pkl, models/label_encoder.pkl

Usage:
    python ml/train_classifier.py
"""

import os
import re
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE

# ── Config ─────────────────────────────────────────────────────────────────────

DATA_PATH   = "data/issues_labeled_clean.csv"
MODELS_DIR  = "models"
RANDOM_SEED = 42

os.makedirs(MODELS_DIR, exist_ok=True)

# ── 1. Load Data ───────────────────────────────────────────────────────────────

print("Loading dataset...")
df = pd.read_csv(DATA_PATH)
print(f"  Total rows    : {len(df)}")
print(f"  Class counts  :\n{df['difficulty_label'].value_counts()}\n")

# ── 2. Preprocessing ───────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Lowercase, strip URLs, markdown noise, extra whitespace."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", " ", text)           # remove URLs
    text = re.sub(r"```[\s\S]*?```", " code ", text)  # replace code blocks
    text = re.sub(r"[^a-z0-9\s\-_]", " ", text)   # keep alphanumeric
    text = re.sub(r"\s+", " ", text).strip()
    return text

def build_combined_text(row) -> str:
    """
    Combine title + body.
    Title is repeated 3x to give it more weight (TF-IDF is bag-of-words).
    """
    title  = clean_text(str(row.get("title", "")))
    body   = clean_text(str(row.get("body", "")))
    # Truncate body to 500 chars to avoid very long docs dominating
    body   = body[:500]
    return f"{title} {title} {title} {body}".strip()

print("Building combined text features...")
df = df.dropna(subset=["difficulty_label"])
df["difficulty_label"] = df["difficulty_label"].astype(str).str.strip().str.title()
df["text"] = df.apply(build_combined_text, axis=1)

# Drop rows where text is essentially empty
df = df[df["text"].str.len() > 10].reset_index(drop=True)
print(f"  Rows after cleaning: {len(df)}\n")

# ── 3. Encode Labels ───────────────────────────────────────────────────────────

le = LabelEncoder()
le.fit(["Beginner", "Intermediate", "Advanced"])
df["label_encoded"] = le.transform(df["difficulty_label"])

print(f"Label mapping: {dict(zip(le.classes_, le.transform(le.classes_)))}\n")

# ── 4. Train / Test Split ──────────────────────────────────────────────────────

X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    df["text"],
    df["label_encoded"],
    test_size=0.20,
    random_state=RANDOM_SEED,
    stratify=df["label_encoded"],   # keep class ratio in both splits
)

print(f"Train size : {len(X_train_raw)}")
print(f"Test  size : {len(X_test_raw)}\n")

# ── 5. TF-IDF Vectorization ────────────────────────────────────────────────────

print("Fitting TF-IDF vectorizer...")
tfidf = TfidfVectorizer(
    max_features=15_000,
    ngram_range=(1, 2),       # unigrams + bigrams
    sublinear_tf=True,        # apply log(tf) — helps with long docs
    min_df=3,                 # ignore very rare terms
    max_df=0.95,              # ignore terms that appear in >95% docs
    strip_accents="unicode",
    analyzer="word",
)

X_train = tfidf.fit_transform(X_train_raw)
X_test  = tfidf.transform(X_test_raw)
print(f"  Vocabulary size: {len(tfidf.vocabulary_)}\n")

# ── 6. Handle Class Imbalance with SMOTE ──────────────────────────────────────
# Beginner=18627, Intermediate=6728, Advanced=4588 → imbalanced
# SMOTE oversamples minority classes so model doesn't just predict Beginner

print("Applying SMOTE to balance classes...")
smote = SMOTE(random_state=RANDOM_SEED, k_neighbors=5)
X_train_bal, y_train_bal = smote.fit_resample(X_train, y_train)

unique, counts = np.unique(y_train_bal, return_counts=True)
for cls, cnt in zip(le.classes_[unique], counts):
    print(f"  {cls}: {cnt}")
print()

# ── 7. Train XGBoost ──────────────────────────────────────────────────────────

print("Training XGBoost classifier...")
model = XGBClassifier(
    n_estimators=400,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    use_label_encoder=False,
    eval_metric="mlogloss",
    random_state=RANDOM_SEED,
    n_jobs=-1,                # use all CPU cores
    tree_method="hist",       # fast histogram method
)

model.fit(
    X_train_bal,
    y_train_bal,
    eval_set=[(X_test, y_test)],
    verbose=50,
)

# ── 8. Evaluate ────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print("EVALUATION ON HELD-OUT TEST SET")
print("="*60)

y_pred = model.predict(X_test)
acc    = accuracy_score(y_test, y_pred)

print(f"\nOverall Accuracy: {acc * 100:.2f}%\n")

if acc < 0.80:
    print("⚠️  WARNING: Accuracy below 80%. Consider:")
    print("   - Increasing n_estimators to 600")
    print("   - Increasing max_features in TF-IDF to 20000")
    print("   - Cleaning the dataset for mislabeled samples")
else:
    print("✅  Accuracy target met (≥80%)")

print("\nPer-class Report:")
print(classification_report(
    y_test, y_pred,
    target_names=le.classes_,
    digits=3,
))

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots(figsize=(7, 5))
sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=le.classes_,
    yticklabels=le.classes_,
    ax=ax,
)
ax.set_xlabel("Predicted Label")
ax.set_ylabel("True Label")
ax.set_title(f"Confusion Matrix — Accuracy: {acc*100:.2f}%")
plt.tight_layout()
cm_path = os.path.join(MODELS_DIR, "confusion_matrix.png")
plt.savefig(cm_path, dpi=150)
print(f"\nConfusion matrix saved to: {cm_path}")

# ── 9. Save Models ─────────────────────────────────────────────────────────────

print("\nSaving models...")
joblib.dump(model, os.path.join(MODELS_DIR, "classifier.pkl"))
joblib.dump(tfidf, os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl"))
joblib.dump(le,    os.path.join(MODELS_DIR, "label_encoder.pkl"))

print("  ✅ models/classifier.pkl")
print("  ✅ models/tfidf_vectorizer.pkl")
print("  ✅ models/label_encoder.pkl")
print("\nTraining complete. Run ml_service.py to verify load.")

