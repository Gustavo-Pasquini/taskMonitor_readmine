import requests
from config import SECRET_REDMINE_URL, SECRET_API_KEY

REDMINE_URL = SECRET_REDMINE_URL
API_KEY     = SECRET_API_KEY


def _headers():
    return {"X-Redmine-API-Key": API_KEY}


def get_current_user():
    r = requests.get(f"{REDMINE_URL}/users/current.json", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()["user"]


def get_statuses():
    r = requests.get(f"{REDMINE_URL}/issue_statuses.json", headers=_headers(), timeout=10)
    r.raise_for_status()
    return {s["name"]: s["id"] for s in r.json()["issue_statuses"]}


def get_issues(user_id, status_id="*", limit=100, offset=0):
    r = requests.get(
        f"{REDMINE_URL}/issues.json",
        headers=_headers(),
        params={"assigned_to_id": user_id, "status_id": status_id, "limit": limit, "offset": offset},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def get_all_issues(user_id, status_id="*"):
    all_issues = []
    offset     = 0
    while True:
        data   = get_issues(user_id, status_id=status_id, limit=100, offset=offset)
        issues = data.get("issues", [])
        all_issues.extend(issues)
        if len(all_issues) >= data.get("total_count", 0):
            break
        offset += 100
    return all_issues


def get_issue_with_journals(issue_id):
    r = requests.get(
        f"{REDMINE_URL}/issues/{issue_id}.json",
        headers=_headers(),
        params={"include": "journals"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["issue"]
