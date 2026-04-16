"""
generate_training_data.py
Generates synthetic GitHub issue training data for ML model training.
Replaces the BigQuery fetch that hits GCP free quota limits.
Run from project root: python data/generate_training_data.py
"""

import pandas as pd
import random
import os

random.seed(42)

BEGINNER_TITLES = [
    "Fix typo in README", "Update documentation", "Add missing docstring",
    "Fix broken link in docs", "Add example to README", "Fix indentation",
    "Rename variable for clarity", "Add comments to code", "Fix spelling mistake",
    "Update changelog", "Add .gitignore entry", "Fix formatting issue",
]
INTERMEDIATE_TITLES = [
    "Add unit tests for auth module", "Refactor database query",
    "Implement pagination for API", "Add input validation",
    "Fix memory leak in worker", "Add error handling to fetch",
    "Optimize slow SQL query", "Add caching layer", "Fix race condition",
    "Implement retry logic", "Add logging to pipeline",
]
ADVANCED_TITLES = [
    "Implement OAuth2 flow", "Add WebSocket support", "Design new DB schema",
    "Build recommendation engine", "Migrate to async architecture",
    "Implement distributed locking", "Add full-text search", "Build ML pipeline",
    "Refactor monolith to microservices", "Implement rate limiting",
]

LANGUAGES = ["Python", "JavaScript", "TypeScript", "Go", "Java", "Ruby", "Rust", "C++"]
LABELS_MAP = {
    "beginner":     ["good first issue", "documentation", "help wanted", "easy"],
    "intermediate": ["bug", "enhancement", "help wanted", "needs tests"],
    "advanced":     ["architecture", "performance", "security", "complex", "refactor"],
}

def make_row(difficulty):
    if difficulty == "beginner":
        title = random.choice(BEGINNER_TITLES) + f" #{random.randint(1,999)}"
        comment_count = random.randint(0, 5)
        days_open = random.randint(1, 30)
        body_length = random.randint(20, 200)
        num_labels = random.randint(1, 2)
    elif difficulty == "intermediate":
        title = random.choice(INTERMEDIATE_TITLES) + f" #{random.randint(1,999)}"
        comment_count = random.randint(3, 15)
        days_open = random.randint(5, 90)
        body_length = random.randint(150, 600)
        num_labels = random.randint(1, 3)
    else:
        title = random.choice(ADVANCED_TITLES) + f" #{random.randint(1,999)}"
        comment_count = random.randint(8, 40)
        days_open = random.randint(14, 180)
        body_length = random.randint(400, 1500)
        num_labels = random.randint(2, 4)

    labels = random.sample(LABELS_MAP[difficulty], min(num_labels, len(LABELS_MAP[difficulty])))

    return {
        "title": title,
        "body_length": body_length,
        "comment_count": comment_count,
        "days_open": days_open,
        "num_labels": num_labels,
        "language": random.choice(LANGUAGES),
        "has_good_first_issue": int("good first issue" in labels),
        "labels": ",".join(labels),
        "difficulty": difficulty,
    }

def generate(n=50000):
    print("Generating synthetic training data...")
    rows = []
    # Balanced classes: ~40% beginner, 35% intermediate, 25% advanced
    for _ in range(int(n * 0.40)): rows.append(make_row("beginner"))
    for _ in range(int(n * 0.35)): rows.append(make_row("intermediate"))
    for _ in range(int(n * 0.25)): rows.append(make_row("advanced"))
    random.shuffle(rows)
    return pd.DataFrame(rows)

if __name__ == "__main__":
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    df = generate(50000)

    raw_path = "data/raw/gh_archive_raw.csv"
    processed_path = "data/processed/training_data.csv"

    df.to_csv(raw_path, index=False)
    print(f"Raw data saved:       {raw_path}  ({len(df)} rows)")

    df.to_csv(processed_path, index=False)
    print(f"Processed data saved: {processed_path}  ({len(df)} rows)")

    print("\nClass distribution:")
    print(df["difficulty"].value_counts().to_string())
    print("\nSample columns:", list(df.columns))
    print("\nDone! Member 2 can now use data/processed/training_data.csv for XGBoost training.")
