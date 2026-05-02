import pandas as pd
import random
import sys

# Force UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE  = "data/issues_labeled.csv"
OUTPUT_FILE = "data/issues_labeled_clean.csv"
CHUNK_SIZE  = 10_000

# ── keyword lists ──────────────────────────────────────────────────────────────
bot_title_keywords = [
    'dependency dashboard', 'renovate', 'dependabot',
    'happy new year', '[bounty]', 'tutorial page',
    'qa orange', 'qa green', 'public thread',
    'issues digest', 'release:', 'studio plans,',
    'dependency review', 'auto comment'
]

uptime_keywords = [
    'is down', 'has degraded', 'is up',
    'http code: 0', 'response time: 0 ms',
    'was down', 'was up'
]

bot_body_keywords = [
    'this issue lists renovate',
    'renovate updates and detected dependencies',
    'affected server: qa',
    'no prs in v',
    'required reviews',
    'public thread',
    'message 6c366'
]

VALID_LABELS = {'beginner', 'intermediate', 'advanced'}

# ── filter function ────────────────────────────────────────────────────────────
def filter_chunk(df: pd.DataFrame) -> pd.DataFrame:
    title = df['title'].fillna('').astype(str)
    body  = df['body'].fillna('').astype(str)
    diff  = df['difficulty_label'].fillna('').astype(str)

    title_lower = title.str.lower()
    body_lower  = body.str.lower()
    diff_lower  = diff.str.lower()

    # 1. NaN / empty title or body
    mask = (title.str.strip() != '') & (body.str.strip() != '')

    # 2. Minimum lengths
    mask &= title.str.strip().str.len() >= 10
    mask &= body.str.strip().str.len() >= 150

    # 3. Valid difficulty label
    mask &= diff_lower.isin(VALID_LABELS)

    # 4. Bot title keywords
    for kw in bot_title_keywords:
        mask &= ~title_lower.str.contains(kw, regex=False, na=False)

    # 5. Uptime title keywords
    for kw in uptime_keywords:
        mask &= ~title_lower.str.contains(kw, regex=False, na=False)

    # 6. Bot body keywords
    for kw in bot_body_keywords:
        mask &= ~body_lower.str.contains(kw, regex=False, na=False)

    # 7. Non-ASCII > 30 % of title
    def high_non_ascii(s: str) -> bool:
        t = str(s)
        non_ascii = sum(1 for c in t if ord(c) > 127)
        return non_ascii / max(len(t), 1) > 0.3

    ascii_ok = title.apply(lambda s: not high_non_ascii(s))
    mask &= ascii_ok

    return df[mask]

# ── Step 1 – quick sample & distribution ──────────────────────────────────────
print("=" * 60)
print("STEP 1 — Analyzing dataset …")
print("=" * 60)

sample_rows = []
total_rows  = 0
label_counts_raw = {}

for chunk in pd.read_csv(
    INPUT_FILE, chunksize=CHUNK_SIZE,
    encoding='utf-8', encoding_errors='ignore', low_memory=False
):
    total_rows += len(chunk)
    sample_rows.extend(chunk[['title', 'difficulty_label']].to_dict('records'))

    for lbl in chunk['difficulty_label'].fillna('MISSING').str.lower():
        label_counts_raw[lbl] = label_counts_raw.get(lbl, 0) + 1

# random sample of 20
random.seed(42)
sample = random.sample(sample_rows, min(20, len(sample_rows)))

print(f"\nTotal rows in original file: {total_rows:,}\n")
print("Random 20-row sample (title | difficulty_label):")
print("-" * 60)
for r in sample:
    title_preview = str(r['title'])[:70].encode('utf-8', errors='replace').decode('utf-8').ljust(72)
    label = str(r['difficulty_label']).encode('utf-8', errors='replace').decode('utf-8')
    print(f"  {title_preview}| {label}")

print("\nRaw difficulty_label distribution:")
for k, v in sorted(label_counts_raw.items(), key=lambda x: -x[1]):
    print(f"  {k:<20}: {v:>10,}")

# ── Step 2 & 3 – filter + deduplicate ─────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2 & 3 — Filtering and deduplicating …")
print("=" * 60)

filtered_chunks = []
rows_after_filter = 0

for i, chunk in enumerate(
    pd.read_csv(
        INPUT_FILE, chunksize=CHUNK_SIZE,
        encoding='utf-8', encoding_errors='ignore', low_memory=False
    ),
    start=1
):
    clean = filter_chunk(chunk)
    filtered_chunks.append(clean)
    rows_after_filter += len(clean)

    if i % 10 == 0:
        print(f"  Processed {i * CHUNK_SIZE:>10,} rows so far …", flush=True)

print(f"  Done. Rows surviving filter: {rows_after_filter:,}")

# Combine and deduplicate on 'url'
print("  Combining chunks …")
combined = pd.concat(filtered_chunks, ignore_index=True)

before_dedup = len(combined)
combined.drop_duplicates(subset='url', keep='first', inplace=True)
after_dedup  = len(combined)
dupes_removed = before_dedup - after_dedup
print(f"  Duplicates removed: {dupes_removed:,}")

# ── Step 4 – save & report ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4 — Saving and final report")
print("=" * 60)

combined.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
print(f"  Saved → {OUTPUT_FILE}")

final_dist = combined['difficulty_label'].str.lower().value_counts()

print(f"""
  Original rows   : {total_rows:>10,}
  Rows removed    : {total_rows - rows_after_filter:>10,}
  Duplicates removed: {dupes_removed:>8,}
  Final clean rows: {after_dedup:>10,}

  Final distribution:
    Beginner     : {final_dist.get('beginner', 0):>10,}
    Intermediate : {final_dist.get('intermediate', 0):>10,}
    Advanced     : {final_dist.get('advanced', 0):>10,}
""")
print("Done ✓")
