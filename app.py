from datetime import datetime
import re
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Curated Climate & Development Roles",
    page_icon="🌱",
    layout="wide",
)

# ---------------------------------------------------------
# TARGETED PROFILE CONFIGURATION (ALIGNED TO YOUR CV)
# ---------------------------------------------------------

# Roles you are qualified for: Research, Management, Strategy, Policy, ESG, Advisory
TARGET_TITLE_KEYWORDS = [
    "adaptation",
    "resilience",
    "carbon",
    "vcm",
    "climate finance",
    "climate policy",
    "climate change",
    "esg",
    "sustainability",
    "sustainable development",
    "political ecology",
    "loss and damage",
    "nature-based",
    "decentralised energy",
    "program manager",
    "project manager",
    "research officer",
    "research manager",
    "insights manager",
    "consultant",
    "analyst",
    "associate",
    "advisor",
    "specialist",
    "lead",
]

# Sectors / Technical themes
DOMAIN_KEYWORDS = [
    "climate adaptation",
    "community resilience",
    "vulnerability assessment",
    "carbon market",
    "vcm",
    "ghg",
    "carbon credits",
    "climate risk",
    "climate finance",
    "multilateral",
    "fao",
    "agroecology",
    "renewable energy",
    "environmental policy",
    "just transition",
    "degrowth",
    "loss and damage",
    "development studies",
    "stakeholder engagement",
]

# Specific target locations & work arrangements
LOCATION_KEYWORDS = [
    "remote",
    "worldwide",
    "anywhere",
    "india",
    "bangalore",
    "bengaluru",
    "kochi",
    "cochin",
    "kerala",
    "delhi",
    "new delhi",
    "thailand",
    "sri lanka",
    "global",
    "hybrid",
    "visa sponsorship",
    "visa",
]

# Strict blocklist to filter out engineering, software, medical/clinical, and irrelevant professions
EXCLUDED_KEYWORDS = [
    "software engineer",
    "devops",
    "full stack",
    "backend",
    "frontend",
    "hardware",
    "mechanical engineer",
    "civil engineer",
    "electrical engineer",
    "site reliability",
    "psychologist",
    "psychiatrist",
    "mental health",
    "nurse",
    "doctor",
    "clinical",
    "therapist",
    "internship",
    "intern",
    "entry level",
    "graduate trainee",
    "unpaid",
    "graphic designer",
    "sales representative",
    "telecaller",
]


def is_strong_match(title: str, text: str, location: str) -> bool:
    """Evaluates if the role matches your specific background and excludes irrelevant roles."""
    combined = f"{title} {text} {location}".lower()
    title_lower = title.lower()

    # 1. Hard filter: Reject any excluded titles or terms
    for bad_term in EXCLUDED_KEYWORDS:
        if re.search(rf"\b{re.escape(bad_term)}\b", combined):
            return False

    # 2. Location check
    has_target_location = any(
        loc in combined for loc in LOCATION_KEYWORDS
    ) or any(loc in location.lower() for loc in LOCATION_KEYWORDS)
    if not has_target_location:
        return False

    # 3. Title check: Title must match at least one relevant role/title type
    has_title_match = any(tk in title_lower for tk in TARGET_TITLE_KEYWORDS)

    # 4. Domain check: Full posting must match core climate/development themes
    has_domain_match = any(dk in combined for dk in DOMAIN_KEYWORDS)

    return has_title_match and has_domain_match


# ---------------------------------------------------------
# FETCHERS
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_curated_jobs():
    matched_jobs = []

    # Source 1: ReliefWeb (Development Sector, FAO, Multilateral, NGOs)
    try:
        url = "https://api.reliefweb.int/v1/jobs?appname=climate-curator&limit=60&preset=latest"
        res = requests.get(url, timeout=12).json()
        for item in res.get("data", []):
            fields = item.get("fields", {})
            title = fields.get("title", "")
            body = fields.get("body", "")
            country_names = [
                c.get("name", "") for c in fields.get("country", [])
            ]
            location = (
                ", ".join(country_names)
                if country_names
                else "Global / Remote / Multiple"
            )
            org_name = (
                fields.get("source", [{}])[0].get("name", "International Org")
                if fields.get("source")
                else "International Org"
            )
            link = fields.get("url", item.get("href", ""))

            if is_strong_match(title, body, location):
                matched_jobs.append({
                    "Title": title,
                    "Organization": org_name,
                    "Location": location,
                    "Source": "ReliefWeb (Development/Multilateral)",
                    "URL": link,
                })
    except Exception:
        pass

    # Source 2: Climate & Sustainability Greenhouse Boards
    # Targeted organizations in climate tech, research, and advisory
    org_boards = [
        ("climateworksfoundation", "ClimateWorks Foundation"),
        ("rockymountaininstitute", "Rocky Mountain Institute (RMI)"),
        ("worldresourcesinstitute", "World Resources Institute (WRI)"),
        ("c40cities", "C40 Cities"),
        ("systemiq", "Systemiq"),
        ("carbontracker", "Carbon Tracker"),
    ]

    for org_id, org_name in org_boards:
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{org_id}/jobs"
            res = requests.get(url, timeout=8).json()
            for job in res.get("jobs", []):
                title = job.get("title", "")
                loc = job.get("location", {}).get("name", "Remote / Hybrid")
                link = job.get("absolute_url", "")
                if is_strong_match(title, "", loc):
                    matched_jobs.append({
                        "Title": title,
                        "Organization": org_name,
                        "Location": loc,
                        "Source": "Direct Organization Board",
                        "URL": link,
                    })
        except Exception:
            pass

    return pd.DataFrame(matched_jobs)


# ---------------------------------------------------------
# STREAMLIT UI
# ---------------------------------------------------------
st.title("🌱 Climate Adaptation & Sustainability Opportunities")
st.caption(
    "Curated specifically for mid/senior roles in Adaptation, Resilience, VCM, Climate Finance & Policy Research."
)

with st.spinner("Screening recent listings for qualified roles..."):
    df = fetch_curated_jobs()

# Sidebar filters
st.sidebar.header("Filter & Search")
search_query = st.sidebar.text_input(
    "Search keyword",
    placeholder="e.g., Adaptation, VCM, Finance, Research, Manager",
)

if not df.empty:
    if search_query:
        df = df[
            df["Title"].str.contains(search_query, case=False, na=False)
            | df["Organization"].str.contains(search_query, case=False, na=False)
            | df["Location"].str.contains(search_query, case=False, na=False)
        ]

    st.subheader(f"✨ Found {len(df)} Roles Matching Your Background")

    for _, row in df.iterrows():
        with st.container():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"### {row['Title']}")
                st.markdown(
                    f"**Organization:** `{row['Organization']}` &nbsp;|&nbsp; 📍 **Location:** {row['Location']} &nbsp;|&nbsp; 🌐 **Source:** {row['Source']}"
                )
            with c2:
                st.link_button(
                    "View Role ↗", row["URL"], use_container_width=True
                )
            st.divider()

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        "📥 Download CSV",
        data=csv_data,
        file_name=f"curated_climate_jobs_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
else:
    st.info(
        "No new jobs matched the criteria during this refresh. Check back later or adjust keywords."
    )
