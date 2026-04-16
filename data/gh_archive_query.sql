-- ── gh_archive_query.sql ────────────────────────────────────────
-- Queries GH Archive on BigQuery to get resolved issues
-- + the contributor who solved them
-- + their prior merged PR count (used for difficulty labeling)
--
-- HOW TO USE:
--   1. Go to https://console.cloud.google.com/bigquery
--   2. Paste this query
--   3. Run it (first 1TB/month is free)
--   4. Export results as CSV to data/raw/gh_archive_raw.csv
--
-- TARGET: 50,000+ labeled issues
-- DATE RANGE: Adjust the date filter below to get more/less data
-- ────────────────────────────────────────────────────────────────

WITH

-- Step 1: Get all closed issues with their resolver
closed_issues AS (
  SELECT
    JSON_VALUE(payload, '$.issue.id')           AS github_issue_id,
    JSON_VALUE(payload, '$.issue.title')        AS title,
    JSON_VALUE(payload, '$.issue.body')         AS description,
    JSON_VALUE(payload, '$.issue.user.login')   AS issue_author,
    JSON_VALUE(payload, '$.sender.login')       AS resolver,
    repo.name                                   AS repo_full_name,
    JSON_VALUE(payload, '$.issue.comments')     AS comment_count,
    JSON_VALUE(payload, '$.issue.created_at')   AS issue_created_at,
    created_at                                  AS closed_at,
    TIMESTAMP_DIFF(
      created_at,
      TIMESTAMP(JSON_VALUE(payload, '$.issue.created_at')),
      DAY
    )                                           AS days_open
  FROM
    `githubarchive.day.201*`   -- covers 2010-2019, adjust as needed
  WHERE
    type = 'IssuesEvent'
    AND JSON_VALUE(payload, '$.action') = 'closed'
    AND JSON_VALUE(payload, '$.issue.state_reason') = 'completed'
    AND JSON_VALUE(payload, '$.issue.title') IS NOT NULL
    AND JSON_VALUE(payload, '$.issue.body') IS NOT NULL
    AND DATE(created_at) BETWEEN '2018-01-01' AND '2020-12-31'
),

-- Step 2: Count prior merged PRs per contributor BEFORE the issue was closed
-- This is the difficulty signal:
--   <= 3 prior merged PRs  → Beginner
--    4-20 prior merged PRs → Intermediate
--   > 20 prior merged PRs  → Advanced
contributor_experience AS (
  SELECT
    actor.login                                 AS contributor,
    COUNT(*)                                    AS prior_merged_prs,
    MIN(created_at)                             AS first_pr_at,
    MAX(created_at)                             AS last_pr_at
  FROM
    `githubarchive.day.201*`
  WHERE
    type = 'PullRequestEvent'
    AND JSON_VALUE(payload, '$.action') = 'closed'
    AND JSON_VALUE(payload, '$.pull_request.merged') = 'true'
    AND DATE(created_at) BETWEEN '2015-01-01' AND '2020-12-31'
  GROUP BY
    actor.login
),

-- Step 3: Join issues with contributor experience
labeled_issues AS (
  SELECT
    ci.github_issue_id,
    ci.title,
    ci.description,
    ci.repo_full_name,
    ci.resolver,
    ci.comment_count,
    ci.days_open,
    ci.issue_created_at,
    ci.closed_at,
    COALESCE(ce.prior_merged_prs, 0)            AS resolver_prior_prs,

    -- Difficulty label (proxy from contributor experience)
    CASE
      WHEN COALESCE(ce.prior_merged_prs, 0) <= 3  THEN 'beginner'
      WHEN COALESCE(ce.prior_merged_prs, 0) <= 20 THEN 'intermediate'
      ELSE 'advanced'
    END                                         AS difficulty,

    -- Extra features for XGBoost (Member 2 uses these)
    LENGTH(ci.title)                            AS title_length,
    LENGTH(COALESCE(ci.description, ''))        AS description_length,
    (
      SELECT COUNT(*)
      FROM UNNEST(SPLIT(COALESCE(ci.description, ''), '```')) AS chunk
      WITH OFFSET pos WHERE MOD(pos, 2) = 1
    )                                           AS code_block_count,
    CAST(ci.comment_count AS INT64)             AS comment_count_int

  FROM
    closed_issues ci
  LEFT JOIN
    contributor_experience ce ON ci.resolver = ce.contributor
  WHERE
    ci.title IS NOT NULL
    AND LENGTH(ci.title) > 10
    AND LENGTH(COALESCE(ci.description, '')) > 20
)

-- Final output
SELECT
  github_issue_id,
  title,
  description,
  repo_full_name,
  resolver,
  resolver_prior_prs,
  difficulty,
  title_length,
  description_length,
  code_block_count,
  comment_count_int         AS comment_count,
  days_open,
  issue_created_at,
  closed_at
FROM
  labeled_issues
ORDER BY
  RAND()                   -- randomize order for better training splits
LIMIT 60000                -- target 50k+ with buffer for filtering
