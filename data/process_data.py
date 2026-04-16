# ── process_data.py ──────────────────────────────────────────────
# Cleans and processes raw GH Archive data
# Outputs final training CSV for Member 2's ML models
#
# INPUT:  data/raw/gh_archive_raw.csv
# OUTPUT: data/processed/training_data.csv
#         data/processed/data_stats.json
#
# USAGE:
#   python data/process_data.py
# ────────────────────────────────────────────────────────────────

import json
import re
import pandas as pd
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────

RAW_FILE        = Path(__file__).parent / "raw" / "gh_archive_raw.csv"
PROCESSED_DIR   = Path(__file__).parent / "processed"
OUTPUT_FILE     = PROCESSED_DIR / "training_data.csv"
STATS_FILE      = PROCESSED_DIR / "data_stats.json"

MIN_TITLE_LEN   = 10
MIN_DESC_LEN    = 20
MAX_DESC_LEN    = 10_000   # truncate very long descriptions


# ── Cleaning functions ───────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Clean issue title/description text.
    Removes excessive whitespace, normalizes newlines.
    Keeps code blocks (important signal for difficulty classifier).
    """
    if not isinstance(text, str):
        return ""
    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Remove null bytes
    text = text.replace("\x00", "")
    # Collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def count_code_blocks(text: str) -> int:
    """Count number of ``` code blocks in text."""
    if not isinstance(text, str):
        return 0
    return text.count("```") // 2


def count_linked_issues(text: str) -> int:
    """Count #123 style issue references in text."""
    if not isinstance(text, str):
        return 0
    return len(re.findall(r"#\d+", text))


def process(df: pd.DataFrame) -> pd.DataFrame:
    print(f"Starting with {len(df):,} rows")

    # ── 1. Drop nulls ────────────────────────────────────────────
    df = df.dropna(subset=["title", "difficulty"])
    print(f"After dropping nulls: {len(df):,} rows")

    # ── 2. Clean text fields ─────────────────────────────────────
    df["title"]       = df["title"].apply(clean_text)
    df["description"] = df["description"].fillna("").apply(clean_text)

    # ── 3. Filter by length ──────────────────────────────────────
    df = df[df["title"].str.len() >= MIN_TITLE_LEN]
    df = df[df["description"].str.len() >= MIN_DESC_LEN]
    print(f"After length filter: {len(df):,} rows")

    # ── 4. Truncate long descriptions ────────────────────────────
    df["description"] = df["description"].str[:MAX_DESC_LEN]

    # ── 5. Add computed features for XGBoost ─────────────────────
    df["title_char_count"]       = df["title"].str.len()
    df["description_char_count"] = df["description"].str.len()
    df["code_block_count"]       = df["description"].apply(count_code_blocks)
    df["linked_issue_count"]     = df["description"].apply(count_linked_issues)

    # ── 6. Fill numeric nulls ────────────────────────────────────
    df["comment_count"]  = df["comment_count"].fillna(0).astype(int)
    df["days_open"]      = df["days_open"].fillna(0).astype(int)
    df["resolver_prior_prs"] = df["resolver_prior_prs"].fillna(0).astype(int)

    # ── 7. Validate difficulty labels ────────────────────────────
    valid_labels = {"beginner", "intermediate", "advanced"}
    df = df[df["difficulty"].isin(valid_labels)]
    print(f"After label validation: {len(df):,} rows")

    # ── 8. Remove duplicates ─────────────────────────────────────
    df = df.drop_duplicates(subset=["github_issue_id"])
    print(f"After deduplication: {len(df):,} rows")

    # ── 9. Shuffle for better train/val/test splits ───────────────
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    return df


def save_stats(df: pd.DataFrame) -> None:
    """Save dataset statistics for Member 2's reference."""
    stats = {
        "total_rows": len(df),
        "difficulty_distribution": df["difficulty"].value_counts().to_dict(),
        "difficulty_percentages": (
            df["difficulty"].value_counts(normalize=True) * 100
        ).round(1).to_dict(),
        "avg_title_length":       round(df["title_char_count"].mean(), 1),
        "avg_description_length": round(df["description_char_count"].mean(), 1),
        "avg_code_blocks":        round(df["code_block_count"].mean(), 2),
        "avg_days_open":          round(df["days_open"].mean(), 1),
        "avg_comment_count":      round(df["comment_count"].mean(), 1),
        "columns":                list(df.columns),
    }
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Stats saved to: {STATS_FILE}")


def print_summary(df: pd.DataFrame) -> None:
    print("\n── Processed Dataset Summary ────────────────────")
    print(f"Total rows:     {len(df):,}")
    print(f"\nDifficulty distribution:")
    dist = df["difficulty"].value_counts()
    for label, count in dist.items():
        pct = count / len(df) * 100
        print(f"  {label:15s}: {count:6,} ({pct:.1f}%)")
    print(f"\nFeature columns for Member 2's XGBoost:")
    feature_cols = [
        "title", "description", "title_char_count",
        "description_char_count", "code_block_count",
        "linked_issue_count", "comment_count",
        "days_open", "resolver_prior_prs"
    ]
    for col in feature_cols:
        print(f"  - {col}")
    print(f"\nLabel column: difficulty")
    print(f"\nSample:")
    print(df[["title", "difficulty", "resolver_prior_prs"]].head(3).to_string())
    print("─────────────────────────────────────────────────")


if __name__ == "__main__":
    print("── GH Archive Data Processor ────────────────────")

    if not RAW_FILE.exists():
        print(f"ERROR: Raw file not found: {RAW_FILE}")
        print("Run fetch_gh_archive.py first")
        raise SystemExit(1)

    print(f"Loading raw data from: {RAW_FILE}")
    df_raw = pd.read_csv(RAW_FILE)
    print(f"Loaded {len(df_raw):,} rows")

    df_processed = process(df_raw)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df_processed.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"\nSaved processed data to: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB")

    save_stats(df_processed)
    print_summary(df_processed)

    print(f"\nDone! Member 2 can now train on: {OUTPUT_FILE}")
    print("Columns Member 2 needs:")
    print("  Features: title, description, title_char_count,")
    print("            description_char_count, code_block_count,")
    print("            linked_issue_count, comment_count, days_open")
    print("  Label:    difficulty")
