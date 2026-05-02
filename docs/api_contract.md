# OpenSource Companion — API Contract

> **Version:** 1.0  
> **Base URL:** `http://localhost:8000`  
> **Content-Type:** `application/json`

---

## Response Format

All endpoints return a consistent JSON envelope:

```json
{
  "message": "Human-readable status message",
  "data": { }
}
```

On error:

```json
{
  "message": "Error description",
  "data": null
}
```

---

## Authentication

Protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

---

## Endpoints

### 1. POST `/auth/github/callback`

**Description:** Exchanges a GitHub OAuth authorization code for an access token. Creates the user record on first login.

**Auth Required:** No

**Request Body:**

```json
{
  "code": "github_oauth_authorization_code"
}
```

**Response — 200 OK:**

```json
{
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "github_username": "octocat",
      "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
      "skill_level": "beginner",
      "points_total": 0,
      "is_mentor": false
    }
  }
}
```

**Status Codes:**

| Code | Condition |
|------|-----------|
| 200  | Login successful |
| 400  | Missing or invalid `code` |
| 401  | GitHub rejected the authorization code |
| 500  | Internal server error |

---

### 2. POST `/auth/refresh`

**Description:** Issues a new access token using a valid refresh token.

**Auth Required:** No

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response — 200 OK:**

```json
{
  "message": "Token refreshed",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
}
```

**Status Codes:**

| Code | Condition |
|------|-----------|
| 200  | Token refreshed successfully |
| 400  | Missing `refresh_token` |
| 401  | Refresh token is expired or invalid |
| 500  | Internal server error |

---

### 3. POST `/auth/logout`

**Description:** Invalidates the current session and blacklists the refresh token.

**Auth Required:** Yes

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response — 200 OK:**

```json
{
  "message": "Logged out successfully",
  "data": null
}
```

**Status Codes:**

| Code | Condition |
|------|-----------|
| 200  | Logged out successfully |
| 401  | Missing or invalid access token |
| 500  | Internal server error |

---

### 4. GET `/recommendations`

**Description:** Returns a list of recommended GitHub issues for the authenticated user, filtered by skill level and optionally by language.

**Auth Required:** Yes

**Query Parameters:**

| Param      | Type   | Required | Default | Description |
|------------|--------|----------|---------|-------------|
| `language` | string | No       | —       | Filter by programming language (e.g. `python`) |
| `limit`    | int    | No       | 10      | Max results to return (1–50) |
| `offset`   | int    | No       | 0       | Pagination offset |

**Response — 200 OK:**

```json
{
  "message": "Recommendations fetched",
  "data": {
    "total": 42,
    "items": [
      {
        "issue_id": 101,
        "title": "Fix typo in README",
        "description": "There is a typo in the contributing guide...",
        "difficulty": "beginner",
        "language": "python",
        "state": "open",
        "github_url": "https://github.com/owner/repo/issues/5",
        "comment_count": 3,
        "days_open": 12,
        "repo": {
          "full_name": "owner/repo",
          "stars": 1500
        }
      }
    ]
  }
}
```

**Status Codes:**

| Code | Condition |
|------|-----------|
| 200  | Recommendations returned |
| 400  | Invalid query parameters |
| 401  | Missing or invalid access token |
| 500  | Internal server error |

---

### 5. POST `/enrollments`

**Description:** Enrolls the authenticated user in a GitHub issue. The user can only have one active enrollment at a time.

**Auth Required:** Yes

**Request Body:**

```json
{
  "issue_id": 101
}
```

**Response — 201 Created:**

```json
{
  "message": "Enrolled successfully",
  "data": {
    "enrollment_id": 55,
    "user_id": 1,
    "issue_id": 101,
    "status": "enrolled",
    "enrolled_at": "2026-05-01T10:30:00Z"
  }
}
```

**Status Codes:**

| Code | Condition |
|------|-----------|
| 201  | Enrollment created |
| 400  | Invalid `issue_id` or issue is not open |
| 401  | Missing or invalid access token |
| 409  | User already has an active enrollment |
| 500  | Internal server error |

---

### 6. GET `/enrollments/{user_id}`

**Description:** Returns all enrollments for a given user, ordered by most recent first.

**Auth Required:** Yes

**Path Parameters:**

| Param     | Type | Description |
|-----------|------|-------------|
| `user_id` | int  | Target user's ID |

**Query Parameters:**

| Param    | Type   | Required | Default | Description |
|----------|--------|----------|---------|-------------|
| `status` | string | No       | —       | Filter by status: `enrolled`, `completed`, `dropped`, `stale` |

**Response — 200 OK:**

```json
{
  "message": "Enrollments fetched",
  "data": {
    "total": 3,
    "items": [
      {
        "enrollment_id": 55,
        "issue_id": 101,
        "status": "enrolled",
        "pr_url": null,
        "enrolled_at": "2026-05-01T10:30:00Z",
        "completed_at": null,
        "issue": {
          "title": "Fix typo in README",
          "difficulty": "beginner",
          "language": "python",
          "github_url": "https://github.com/owner/repo/issues/5",
          "repo_full_name": "owner/repo"
        }
      },
      {
        "enrollment_id": 40,
        "issue_id": 78,
        "status": "completed",
        "pr_url": "https://github.com/owner/repo/pull/12",
        "enrolled_at": "2026-04-15T08:00:00Z",
        "completed_at": "2026-04-20T14:22:00Z",
        "issue": {
          "title": "Add dark mode toggle",
          "difficulty": "intermediate",
          "language": "javascript",
          "github_url": "https://github.com/owner/repo/issues/9",
          "repo_full_name": "owner/repo"
        }
      }
    ]
  }
}
```

**Status Codes:**

| Code | Condition |
|------|-----------|
| 200  | Enrollments returned |
| 400  | Invalid `status` filter value |
| 401  | Missing or invalid access token |
| 404  | User not found |
| 500  | Internal server error |

---

### 7. POST `/contributions/check`

**Description:** Manually triggers a contribution status check for the authenticated user's active enrollment. Checks if a PR referencing the enrolled issue has been merged.

**Auth Required:** Yes

**Request Body:** None

**Response — 200 OK:**

```json
{
  "message": "Contribution status checked",
  "data": {
    "enrollment_id": 55,
    "previous_status": "enrolled",
    "current_status": "completed",
    "pr_url": "https://github.com/owner/repo/pull/18"
  }
}
```

**Response — 200 OK (no change):**

```json
{
  "message": "No merged PR found yet",
  "data": {
    "enrollment_id": 55,
    "previous_status": "enrolled",
    "current_status": "enrolled",
    "pr_url": null
  }
}
```

**Status Codes:**

| Code | Condition |
|------|-----------|
| 200  | Check completed |
| 401  | Missing or invalid access token |
| 404  | No active enrollment found |
| 500  | Internal server error |

---

### 8. GET `/gamification/leaderboard`

**Description:** Returns the top users ranked by total points.

**Auth Required:** No

**Query Parameters:**

| Param  | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `limit` | int | No       | 10      | Number of users to return (1–100) |

**Response — 200 OK:**

```json
{
  "message": "Leaderboard fetched",
  "data": {
    "items": [
      {
        "rank": 1,
        "user_id": 7,
        "github_username": "alice",
        "avatar_url": "https://avatars.githubusercontent.com/u/7?v=4",
        "points_total": 850,
        "is_mentor": true
      },
      {
        "rank": 2,
        "user_id": 3,
        "github_username": "bob",
        "avatar_url": "https://avatars.githubusercontent.com/u/3?v=4",
        "points_total": 620,
        "is_mentor": false
      }
    ]
  }
}
```

**Status Codes:**

| Code | Condition |
|------|-----------|
| 200  | Leaderboard returned |
| 400  | Invalid `limit` value |
| 500  | Internal server error |

---

### 9. GET `/users/{user_id}/profile`

**Description:** Returns the public profile of a user including stats.

**Auth Required:** Yes

**Path Parameters:**

| Param     | Type | Description |
|-----------|------|-------------|
| `user_id` | int  | Target user's ID |

**Response — 200 OK:**

```json
{
  "message": "Profile fetched",
  "data": {
    "id": 1,
    "github_username": "octocat",
    "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4",
    "skill_level": "intermediate",
    "primary_language": "python",
    "points_total": 350,
    "is_mentor": false,
    "created_at": "2026-03-10T12:00:00Z",
    "stats": {
      "enrollments_completed": 5,
      "enrollments_active": 1,
      "badges_earned": 3
    }
  }
}
```

**Status Codes:**

| Code | Condition |
|------|-----------|
| 200  | Profile returned |
| 401  | Missing or invalid access token |
| 404  | User not found |
| 500  | Internal server error |

---

### 10. GET `/users/{user_id}/badges`

**Description:** Returns all badges earned by a user.

**Auth Required:** Yes

**Path Parameters:**

| Param     | Type | Description |
|-----------|------|-------------|
| `user_id` | int  | Target user's ID |

**Response — 200 OK:**

```json
{
  "message": "Badges fetched",
  "data": {
    "total": 3,
    "items": [
      {
        "badge_id": 1,
        "name": "First Step",
        "description": "Enrolled in your first GitHub issue",
        "icon_url": null,
        "earned_at": "2026-03-10T12:05:00Z"
      },
      {
        "badge_id": 2,
        "name": "First Merge",
        "description": "Got your first pull request merged",
        "icon_url": null,
        "earned_at": "2026-03-15T09:30:00Z"
      },
      {
        "badge_id": 6,
        "name": "Week Warrior",
        "description": "Maintained a 7-day contribution streak",
        "icon_url": null,
        "earned_at": "2026-04-02T18:00:00Z"
      }
    ]
  }
}
```

**Status Codes:**

| Code | Condition |
|------|-----------|
| 200  | Badges returned |
| 401  | Missing or invalid access token |
| 404  | User not found |
| 500  | Internal server error |

---

## Enum Reference

Aligned with `app/models.py`:

| Enum | Values |
|------|--------|
| `SkillLevel` | `beginner`, `intermediate`, `advanced` |
| `Difficulty` | `beginner`, `intermediate`, `advanced` |
| `IssueState` | `open`, `closed` |
| `EnrollmentStatus` | `enrolled`, `completed`, `dropped`, `stale` |
