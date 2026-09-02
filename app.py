import requests
from requests.auth import HTTPBasicAuth
from collections import Counter
from datetime import datetime

# Configuration
JIRA_URL = "https://your-domain.atlassian.net"
EMAIL = "kiran@miqdigital.com"
API_TOKEN = "ATATT3xFfGF0jLXATf907B9oNBnVkK5HeqjgGfzEffWjSFv5isbfp-t0_InsSo9xSAR5bzYZWaSoewYJagfb_8_f0wl1cxYjWYfIgX5ab3fOD7d4NDMmdI4TXZ9bLwnFbKa9xKv7HVKJxNTDEEL9bBGxmYfcMl-tW4Hc-BC8YsupbH5pvnB7XsY=4B03FABA"  # Generate at id.atlassian.net

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {"Accept": "application/json"}

def get_jira_metrics():
    # 1. Count tickets raised today
    jql_today = "created >= startOfDay()"
    res_today = requests.get(
        f"{JIRA_URL}/rest/api/3/search",
        headers=headers,
        auth=auth,
        params={"jql": jql_today, "maxResults": 0}
    )
    tickets_today = res_today.json().get("total", 0)

    # 2. Count tickets worked on today grouped by person
    jql_worked = "updated >= startOfDay()"
    res_worked = requests.get(
        f"{JIRA_URL}/rest/api/3/search",
        headers=headers,
        auth=auth,
        params={"jql": jql_worked, "fields": "assignee", "maxResults": 100}
    )
    
    issues = res_worked.json().get("issues", [])
    assignees = [
        issue["fields"]["assignee"]["displayName"] 
        if issue["fields"].get("assignee") else "Unassigned"
        for issue in issues
    ]
    per_person = Counter(assignees)

    # Display Metrics
    print(f"=== Jira Daily Summary ({datetime.now().strftime('%Y-%m-%d')}) ===")
    print(f"Tickets Raised Today: {tickets_today}\n")
    print("Tickets Worked On Per Person:")
    for person, count in per_person.items():
        print(f" • {person}: {count}")

if __name__ == "__main__":
    get_jira_metrics()
