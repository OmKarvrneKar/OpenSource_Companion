# Data Pipeline — GH Archive

## What this does
Fetches 50,000+ resolved GitHub issues from GH Archive (BigQuery),
labels them by difficulty using contributor experience as a proxy signal,
and outputs a clean CSV for Member 2's ML training pipeline.

## Difficulty labeling logic
| Resolver's prior merged PRs | Label        |
|-----------------------------|--------------|
| 0 – 3                       | beginner     |
| 4 – 20                      | intermediate |
| 21+                         | advanced     |

No manual labeling needed — contributor experience is the signal.

---

## Setup (one time)

### 1. Install dependencies
```bash
pip install google-cloud-bigquery pandas pyarrow
```

### 2. Create GCP project + enable BigQuery
- Go to https://console.cloud.google.com
- Create a new project (or use existing)
- Enable the BigQuery API
- First 1TB/month of queries is FREE

### 3. Create service account credentials
- Go to IAM → Service Accounts → Create Service Account
- Give it BigQuery Data Viewer + BigQuery Job User roles
- Download the JSON key file
- Save it somewhere safe (NOT inside this repo)

### 4. Add to your .env file
```
GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/your-key.json
GCP_PROJECT_ID=your-gcp-project-id
```

---

## Usage

### Step 1 — Fetch raw data from BigQuery
```bash
python data/fetch_gh_archive.py
```
This runs the SQL query and saves to `data/raw/gh_archive_raw.csv`.
Takes 2-5 minutes. Query costs ~$0 (within free tier).

### Step 2 — Process and clean the data
```bash
python data/process_data.py
```
This cleans, filters, and adds features.
Outputs to `data/processed/training_data.csv`.

---

## Output files

| File | Description |
|------|-------------|
| `data/raw/gh_archive_raw.csv` | Raw BigQuery output (60k rows) |
| `data/processed/training_data.csv` | Cleaned training data (50k+ rows) |
| `data/processed/data_stats.json` | Dataset statistics |

---

## For Member 2 (ML)

Your training data is at: `data/processed/training_data.csv`

### Feature columns available for XGBoost:
- `title` — issue title text (use TF-IDF)
- `description` — issue body text (use TF-IDF)
- `title_char_count` — length of title
- `description_char_count` — length of description
- `code_block_count` — number of ``` blocks
- `linked_issue_count` — number of #123 references
- `comment_count` — number of comments on issue
- `days_open` — how long issue was open before resolution

### Label column:
- `difficulty` → `beginner` / `intermediate` / `advanced`

### Quick load:
```python
import pandas as pd
df = pd.read_csv("data/processed/training_data.csv")
X = df[["title", "description", "title_char_count",
        "description_char_count", "code_block_count",
        "linked_issue_count", "comment_count", "days_open"]]
y = df["difficulty"]
```

---

## .gitignore note
`data/raw/` and `data/processed/` are already in `.gitignore`.
Never commit raw data or processed CSVs to Git — they're too large.
