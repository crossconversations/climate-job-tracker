from datetime import datetime
import re
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Climate & Adaptation Jobs", page_icon="🌱", layout="wide"
)

# ---------------------------------------------------------
# PROFILE KEYWORDS & FILTERS
# ---------------------------------------------------------
KEYWORDS = [
    "climate",
    "adaptation",
    "resilience",
    "carbon market",
    "vcm",
    "esg",
    "sustainability",
    "climate finance",
    "political ecology",
    "loss and damage",
    "ghg",
]

LOCATIONS = [
    "remote",
    "worldwide",
    "anywhere",
    "india",
    "bangalore",
    "bengaluru",
    "kochi",
    "cochin",
    "delhi",
    "visa",
]

EXCLUDE = [
    "intern",
    "internship",
    "unpaid",
    "graduate trainee",
    "entry level",
    "entry-level",
]


def matches_profile(text: str) -> bool:
    t = text.lower()
    if any(re.search(rf"\b{re.escape(e)}\b", t) for e in EXCLUDE):
        return False
    return any(k in t for k in KEYWORDS) and any(loc in t for loc in LOCATIONS)


# ---------------------------------------------------------
# FETCHERS
# ---------------------------------------------------------
@st.cache_data(ttl=3600)  # Refreshes data hourly
def load_all_jobs():
    jobs = []

    # 1. ReliefWeb (Multilateral, Climate Adaptation, NGO)
    try:
        url = "https://api.reliefweb.int/v1/jobs?appname=climate-tracker&limit=30&preset=latest"
        res = requests.get(url, timeout=10).json()
        for item in res.get("data", []):
            f = item.get("fields", {})
            title = f.get("title", "")
            body = f.get("body", "")
            country = ", ".join([c.get("name", "") for c in f.get("country", [])])
            loc = country if country else "Global / Remote"
            src = (
                f.get("source", [{}])[0].get("name", "ReliefWeb")
                if f.get("source")
                else "ReliefWeb"
            )
            link = f.get("url", item.get("href", ""))

            if matches_profile(f"{title} {body} {loc}"):
                jobs.append({
                    "Title": title,
                    "Company": src,
                    "Location": loc,
                    "Source": "ReliefWeb",
                    "URL": link,
                })
    except Exception:
        pass

    # 2. Jobicy (Remote Sustainability & Tech)
    try:
        url = "https://jobicy.com/api/v2/remote-jobs?count=40"
        res = requests.get(url, timeout=10).json()
        for item in res.get("jobs", []):
            title = item.get("jobTitle", "")
            desc = item.get("jobDescription", "")
            loc = item.get("jobGeo", "Remote")
            if matches_profile(f"{title} {desc} {loc}"):
                jobs.append({
                    "Title": title,
                    "Company": item.get("companyName", "Unknown"),
                    "Location": loc,
                    "Source": "Jobicy",
                    "URL": item.get("url"),
                })
    except Exception:
        pass

    # 3. Target Climate Orgs (Greenhouse API)
    orgs = ["climateworksfoundation", "rockymountaininstitute"]
    for org in orgs:
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{org}/jobs"
            res = requests.get(url, timeout=8).json()
            for item in res.get("jobs", []):
                title = item.get("title", "")
                loc = item.get("location", {}).get("name", "Remote")
                if matches_profile(f"{title} {loc}"):
                    jobs.append({
                        "Title": title,
                        "Company": org.replace("-", " ").title(),
                        "Location": loc,
                        "Source": "Greenhouse",
                        "URL": item.get("absolute_url"),
                    })
        except Exception:
            pass

    return pd.DataFrame(jobs)


# ---------------------------------------------------------
# USER INTERFACE
# ---------------------------------------------------------
st.title("🌱 Climate & Adaptation Opportunities Portal")
st.markdown(
    "Live-curated openings across **Adaptation, VCM, ESG, and Climate Finance**."
)

with st.spinner("Fetching listings across portals..."):
    df = load_all_jobs()

st.sidebar.header("Filter Results")
search_query = st.sidebar.text_input(
    "Search by Keyword or Title", placeholder="e.g. Adaptation, FAO, Manager"
)

if not df.empty:
    if search_query:
        df = df[
            df["Title"].str.contains(search_query, case=False, na=False)
            | df["Company"].str.contains(search_query, case=False, na=False)
            | df["Location"].str.contains(search_query, case=False, na=False)
        ]

    st.subheader(f"Found {len(df)} matching roles")

    for _, row in df.iterrows():
        with st.container():
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"### {row['Title']}")
                st.markdown(
                    f"**Organization:** {row['Company']} &nbsp;|&nbsp; 📍 **Location:** {row['Location']} &nbsp;|&nbsp; 🔍 **Source:** `{row['Source']}`"
                )
            with c2:
                st.link_button(
                    "Apply ↗", row["URL"], use_container_width=True
                )
            st.divider()

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        "📥 Download Listings as CSV",
        data=csv_data,
        file_name=f"climate_jobs_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
else:
    st.warning("No listings matched your criteria at this moment. Check back soon!")
