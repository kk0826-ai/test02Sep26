import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd

st.set_page_config(page_title="Jira Daily Tracker", page_icon="🎫", layout="wide")

# Safe secret loading
try:
    JIRA_URL = st.secrets["JIRA_URL"].rstrip("/")
    EMAIL = st.secrets["JIRA_EMAIL"]
    API_TOKEN = st.secrets["JIRA_API_TOKEN"]
except Exception:
    st.error("⚠️ Credentials missing. Please configure `.streamlit/secrets.toml`.")
    st.stop()

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {"Accept": "application/json"}

@st.cache_data(ttl=300)
def fetch_jira_data():
    # Query tickets raised today
    created_res = requests.get(
        f"{JIRA_URL}/rest/api/3/search",
        headers=headers,
        auth=auth,
        params={"jql": "created >= startOfDay()", "maxResults": 100, "fields": "summary,assignee,created"},
        timeout=10
    )
    created_res.raise_for_status()

    # Query tickets updated/worked on today
    updated_res = requests.get(
        f"{JIRA_URL}/rest/api/3/search",
        headers=headers,
        auth=auth,
        params={"jql": "updated >= startOfDay()", "maxResults": 100, "fields": "summary,assignee,status,updated"},
        timeout=10
    )
    updated_res.raise_for_status()

    return created_res.json().get("issues", []), updated_res.json().get("issues", [])

# UI Header
st.title("🎫 Jira Daily Activity Dashboard")

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

try:
    with st.spinner("Connecting to Jira API..."):
        created_issues, updated_issues = fetch_jira_data()

    # High-level Metrics
    col1, col2 = st.columns(2)
    col1.metric("Tickets Raised Today", len(created_issues))
    col2.metric("Tickets Worked On Today", len(updated_issues))

    st.divider()

    # Assignee Breakdown Section
    st.subheader("Tickets Worked On Per Person")
    assignees = []
    for issue in updated_issues:
        assignee = issue["fields"].get("assignee")
        name = assignee["displayName"] if assignee else "Unassigned"
        assignees.append(name)

    if assignees:
        df_counts = pd.Series(assignees).value_counts().reset_index()
        df_counts.columns = ["Team Member", "Tickets Worked"]

        chart_col, table_col = st.columns([2, 1])
        with chart_col:
            st.bar_chart(df_counts.set_index("Team Member"))
        with table_col:
            st.dataframe(df_counts, use_container_width=True, hide_index=True)
    else:
        st.info("No tickets updated today yet.")

    st.divider()

    # Detailed Table of Today's Raised Tickets
    st.subheader("Tickets Raised Today")
    if created_issues:
        raised_data = []
        for issue in created_issues:
            fields = issue["fields"]
            assignee = fields.get("assignee")
            raised_data.append({
                "Key": issue["key"],
                "Summary": fields.get("summary"),
                "Assignee": assignee["displayName"] if assignee else "Unassigned"
            })
        st.dataframe(pd.DataFrame(raised_data), use_container_width=True, hide_index=True)
    else:
        st.info("No tickets created today yet.")

except requests.exceptions.Timeout:
    st.error("⏳ Connection timed out. Please check your Jira URL or corporate network/VPN access.")
except requests.exceptions.HTTPError as err:
    st.error(f"🔑 Jira API Error ({err.response.status_code}). Verify your email, API token, and permissions.")
except Exception as e:
    st.error(f"❌ An error occurred: {e}")
