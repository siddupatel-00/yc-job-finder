import os
import sys
import json
import time
import re
import pandas as pd
import streamlit as st

from bright_data import trigger_crawl, poll_dataset, normalize_job_data, DEFAULT_COLLECTOR_ID, DEFAULT_TARGET_URL, test_bright_data_connection
from matcher import rank_and_filter_jobs, parse_keywords
from generator import generate_cold_email_pitch
from analytics import build_salary_distribution_df, build_top_skills_df, get_summary_telemetry
from sample_data import SAMPLE_YC_JOBS

st.set_page_config(
    page_title="YC Job Hunter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# STRICT VERCEL / LINEAR MONOCHROME CSS
# -----------------------------------------------------------------------------




if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "Linear Dark"

is_dark = "Dark" in st.session_state["theme_mode"]

bg_primary = "#000000" if is_dark else "#f8f9fa"
bg_secondary = "#0a0a0a" if is_dark else "#ffffff"
bg_tertiary = "#18181b" if is_dark else "#f1f3f5"
text_primary = "#ededed" if is_dark else "#11181c"
text_secondary = "#a1a1aa" if is_dark else "#687076"
border_color = "#27272a" if is_dark else "#dee2e6"
border_hover = "#3f3f46" if is_dark else "#ced4da"

APP_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp {{
        background-color: {bg_primary} !important;
        color: {text_primary} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }}

    [data-testid="stAppViewBlockContainer"] {{
        background-color: transparent !important;
    }}

    h1, h2, h3, h4, h5, h6, .stMarkdown p strong {{
        color: {text_primary} !important;
    }}
    
    hr {{
        border-color: {border_color} !important;
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {bg_secondary} !important;
        border-right: 1px solid {border_color} !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: {text_secondary} !important;
    }}
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] label {{
        color: {text_primary} !important;
        font-weight: 600 !important;
    }}

    /* Input Fields */
    [data-baseweb="select"] > div, input, textarea {{
        background-color: {bg_secondary} !important;
        color: {text_primary} !important;
        border: 1px solid {border_color} !important;
        border-radius: 6px !important;
    }}
    [data-baseweb="select"] * {{
        color: {text_primary} !important;
    }}
    [data-baseweb="popover"] {{
        background-color: {bg_secondary} !important;
    }}
    
        /* Multiselect Tags (High-Contrast Charcoal Pill) */
    [data-baseweb="tag"],
    div[data-testid="stMultiSelect"] [data-baseweb="tag"],
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"],
    div[data-testid="stMultiSelect"] div[data-baseweb="tag"] {{
        background-color: {"#27272a" if is_dark else "#f4f4f5"} !important;
        background: {"#27272a" if is_dark else "#f4f4f5"} !important;
        border: 1px solid {"#3f3f46" if is_dark else "#e4e4e7"} !important;
        border-radius: 4px !important;
    }}
    [data-baseweb="tag"] *,
    [data-baseweb="tag"] span,
    div[data-testid="stMultiSelect"] [data-baseweb="tag"] *,
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] * {{
        color: {"#ffffff" if is_dark else "#09090b"} !important;
        fill: {"#ffffff" if is_dark else "#09090b"} !important;
    }}

    /* Card Containers */
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        background-color: {bg_secondary} !important;
        border-color: {border_color} !important;
        border-radius: 12px !important;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        border: 1px solid {border_color} !important;
        padding: 4px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    }}

    /* Primary Buttons (Theme toggle, refresh) */
    .stButton > button[kind="primary"], div.top-cta-btn .stButton > button {{
        background-color: {"#ffffff" if is_dark else "#09090b"} !important;
        color: {"#000000" if is_dark else "#ffffff"} !important;
        border: 1px solid {"#ffffff" if is_dark else "#09090b"} !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }}
    .stButton > button[kind="primary"] *, div.top-cta-btn .stButton > button * {{
        color: {"#000000" if is_dark else "#ffffff"} !important;
    }}

    /* Secondary Buttons */
    .stButton > button[kind="secondary"] {{
        background-color: transparent !important;
        color: {text_primary} !important;
        border: 1px solid {border_color} !important;
        border-radius: 6px !important;
    }}
    .stButton > button[kind="secondary"] * {{
        color: {text_primary} !important;
    }}

    /* Link Buttons (Apply -> crisp White button with bold Black text) */
    div[data-testid="stLinkButton"] > a {{
        background-color: {"#ffffff" if is_dark else "#09090b"} !important;
        color: {"#000000" if is_dark else "#ffffff"} !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        text-decoration: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    div[data-testid="stLinkButton"] > a * {{
        color: {"#000000" if is_dark else "#ffffff"} !important;
        font-weight: 600 !important;
    }}

    /* Micro Badges */
    .micro-badge {{
        display: inline-flex;
        align-items: center;
        padding: 3px 8px;
        background: transparent !important;
        color: {text_secondary} !important;
        border: 1px solid {border_color} !important;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 6px;
        margin-top: 3px;
        margin-bottom: 3px;
    }}
    
    .match-badge {{
        color: {"#ffffff" if is_dark else "#09090b"} !important;
        background-color: {"#27272a" if is_dark else "#e4e4e7"} !important;
        border: 1px solid {"#3f3f46" if is_dark else "#d4d4d8"} !important;
        font-weight: 600 !important;
    }}

    .micro-badge-matched {{
        background-color: {"#27272a" if is_dark else "#e4e4e7"} !important;
        color: {"#ffffff" if is_dark else "#09090b"} !important;
        border: 1px solid {"#3f3f46" if is_dark else "#d4d4d8"} !important;
        font-weight: 600 !important;
    }}
    .micro-badge-missing {{
        color: {"#71717a" if is_dark else "#a1a1aa"} !important;
        border-color: {border_color} !important;
    }}

    /* URL-routed Segmented Navigation Tabs (Pill style) */
    div[data-testid="stRadio"] {{
        border: none !important;
        margin-bottom: 16px !important;
    }}
    div[data-testid="stRadio"] > div[role="radiogroup"] {{
        display: flex !important;
        flex-direction: row !important;
        gap: 0.75rem !important;
        background: transparent !important;
    }}
    div[data-testid="stRadio"] label {{
        background: {"#121214" if is_dark else "#f4f4f5"} !important;
        border: 1px solid {border_color} !important;
        border-radius: 6px !important;
        padding: 6px 14px !important;
        cursor: pointer !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: {text_secondary} !important;
        display: flex !important;
        align-items: center !important;
        transition: all 0.15s ease !important;
    }}
    div[data-testid="stRadio"] label:hover {{
        border-color: {border_hover} !important;
        color: {text_primary} !important;
    }}
    div[data-testid="stRadio"] label:hover * {{
        color: {text_primary} !important;
    }}
    div[data-testid="stRadio"] label > div:first-child {{
        display: none !important;
    }}
    div[data-testid="stRadio"] label[data-checked="true"] {{
        background: {"#ffffff" if is_dark else "#09090b"} !important;
        border-color: {"#ffffff" if is_dark else "#09090b"} !important;
        color: {"#000000" if is_dark else "#ffffff"} !important;
    }}
    div[data-testid="stRadio"] label[data-checked="true"] * {{
        color: {"#000000" if is_dark else "#ffffff"} !important;
        font-weight: 600 !important;
    }}

    /* Hide metric deltas */
    [data-testid="stMetricDelta"] {{
        display: none;
    }}

    /* Sidebar Top Spacing & Clean Header */
    section[data-testid="stSidebar"] {{
        padding-top: 0 !important;
    }}
    div[data-testid="stSidebarHeader"] {{
        padding: 0.5rem 1rem 0 1rem !important;
        min-height: 0 !important;
        height: auto !important;
        display: flex !important;
        justify-content: flex-start !important;
    }}
    [data-testid="stSidebarCollapseButton"], 
    section[data-testid="stSidebar"] button[kind="header"] {{
        position: relative !important;
        left: 0 !important;
        top: 0 !important;
        margin: 0 !important;
    }}
    [data-testid="stSidebarUserContent"] {{
        padding-top: 0.25rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    div[data-testid="stSidebarContent"] {{
        padding-top: 0 !important;
    }}

    /* Hide Streamlit default header and footer */
    header[data-testid="stHeader"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    #MainMenu {{
        visibility: hidden !important;
    }}
    footer {{
        visibility: hidden !important;
    }}

    /* Fix top spacing and container padding - full width flush left */
    div.block-container {{
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
        margin-left: 0 !important;
    }}
</style>
"""





st.markdown(APP_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "jobs_data" not in st.session_state:
    st.session_state["jobs_data"] = SAMPLE_YC_JOBS
if "selected_skills" not in st.session_state:
    st.session_state["selected_skills"] = ["Python", "AI"]
if "saved_jobs" not in st.session_state:
    st.session_state["saved_jobs"] = {}

env_token = os.environ.get("BRIGHT_DATA_API_TOKEN", "")

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='font-size: 1.5rem; font-weight: 700; margin-bottom: 0.1rem; padding: 0;'>YC Job Hunter</h2>", unsafe_allow_html=True)
    st.caption("Autonomous startup job intelligence platform.")
    st.markdown("---")

    st.markdown("### Match Preferences")
    location_filter = st.selectbox("Location", ["Any", "Remote Only", "San Francisco, CA", "New York, NY", "Austin, TX"], index=0)
    stage_filter = st.selectbox("Stage", ["Any", "Seed", "Series A", "Series B"], index=0)
    visa_only_toggle = st.checkbox("Visa Sponsorship Only", value=False)
    min_score_filter = st.slider("Min Relevance (%)", 0, 100, 20, 5)
    sort_order = st.selectbox("Sort By", ["Match Score", "Recent", "Company"], index=0)

    st.markdown("---")
    st.markdown("### Crawler Engine")
    crawl_mode = st.radio("Source", ["Live Scraper API", "Instant Cache"], index=0 if env_token else 1, label_visibility="collapsed")
    st.caption("Bright Data DCA Active")


# -----------------------------------------------------------------------------
# TOP TOOLBAR
# -----------------------------------------------------------------------------
col_left_space, col_actions = st.columns([5, 2], vertical_alignment="center")

with col_actions:
    sub1, sub2 = st.columns(2)
    with sub1:
        theme_btn_label = "☀️ Light" if is_dark else "🌙 Dark"
        if st.button(theme_btn_label, key="top_theme_toggle_btn", use_container_width=True):
            st.session_state["theme_mode"] = "Linear Light" if is_dark else "Linear Dark"
            st.rerun()
    with sub2:
        fetch_trigger_btn = st.button("↻ Refresh", use_container_width=True, key="top_fetch_btn")



# -----------------------------------------------------------------------------
# CRAWLER TRIGGER
# -----------------------------------------------------------------------------
if fetch_trigger_btn:
    if "Live" in crawl_mode and env_token:
        with st.status("Fetching live data...", expanded=True) as status:
            success, col_id, _ = trigger_crawl(env_token, DEFAULT_COLLECTOR_ID, DEFAULT_TARGET_URL)
            if success:
                poll_success, raw, _ = poll_dataset(env_token, col_id, max_retries=6, poll_interval_seconds=3)
                if poll_success and raw:
                    st.session_state["jobs_data"] = normalize_job_data(raw)
            status.update(label="Feed updated", state="complete")
    else:
        with st.spinner("Refreshing cache..."):
            time.sleep(0.3)
            st.session_state["jobs_data"] = SAMPLE_YC_JOBS

# -----------------------------------------------------------------------------
# MATCHING LOGIC
# -----------------------------------------------------------------------------
raw_pool = st.session_state["jobs_data"]
active_keywords = parse_keywords(st.session_state["selected_skills"])
scored_jobs = rank_and_filter_jobs(raw_pool, active_keywords, location_filter, stage_filter, visa_only_toggle, min_score_filter)
if sort_order == "Company":
    scored_jobs.sort(key=lambda x: x.get("company", "").lower())
top_score = scored_jobs[0]["match_score"] if scored_jobs else 0
avg_score = int(sum(j["match_score"] for j in scored_jobs) / len(scored_jobs)) if scored_jobs else 0

# -----------------------------------------------------------------------------
# METRICS ROW
# -----------------------------------------------------------------------------
st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
m1, m2, m3 = st.columns(3)
with m1:
    with st.container(border=True):
        st.caption("TOTAL OPPORTUNITIES")
        st.markdown(f"### {len(raw_pool)}")
with m2:
    with st.container(border=True):
        st.caption("MATCHING ROLES")
        st.markdown(f"### {len(scored_jobs)}")
with m3:
    with st.container(border=True):
        st.caption("TOP MATCH FIT")
        st.markdown(f"### {top_score}%")


# -----------------------------------------------------------------------------
# MAIN CONTENT (URL QUERY PARAM DEEP LINKING ROUTING)
# -----------------------------------------------------------------------------
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# Read current active tab from URL query params
current_tab = st.query_params.get("tab", "opportunities")
if current_tab not in ["opportunities", "pitch-generator", "analytics", "terminal"]:
    current_tab = "opportunities"

nav_c1, nav_c2, nav_c3, nav_c4, _ = st.columns([1.6, 1.6, 1.2, 1.2, 3], vertical_alignment="center")

with nav_c1:
    if st.button(
        f"Opportunities ({len(scored_jobs)})", 
        key="nav_btn_opps", 
        type="primary" if current_tab == "opportunities" else "secondary",
        use_container_width=True
    ):
        st.query_params["tab"] = "opportunities"
        st.rerun()

with nav_c2:
    if st.button(
        "Pitch Generator", 
        key="nav_btn_pitch", 
        type="primary" if current_tab == "pitch-generator" else "secondary",
        use_container_width=True
    ):
        st.query_params["tab"] = "pitch-generator"
        st.rerun()

with nav_c3:
    if st.button(
        "Analytics", 
        key="nav_btn_analytics", 
        type="primary" if current_tab == "analytics" else "secondary",
        use_container_width=True
    ):
        st.query_params["tab"] = "analytics"
        st.rerun()

with nav_c4:
    if st.button(
        "Terminal", 
        key="nav_btn_terminal", 
        type="primary" if current_tab == "terminal" else "secondary",
        use_container_width=True
    ):
        st.query_params["tab"] = "terminal"
        st.rerun()

active_tab = current_tab

# =============================================================================
# TAB 1: OPPORTUNITIES
# =============================================================================
if active_tab == "opportunities":
    # Compile comprehensive, dynamic skill pool from dataset + industry standards
    core_skill_set = {
        "Python", "TypeScript", "JavaScript", "Go", "Rust", "C++", "Java", "Solidity", "SQL",
        "AI", "Machine Learning", "LLM", "NLP", "PyTorch", "TensorFlow", "RAG", "LangChain", 
        "Agents", "Computer Vision", "HuggingFace", "Fine-tuning", "VectorDB",
        "React", "Next.js", "Vue", "Node", "FastAPI", "Django", "GraphQL", "TailwindCSS",
        "PostgreSQL", "MongoDB", "Redis", "Kafka", "gRPC", "Distributed Systems",
        "Docker", "Kubernetes", "AWS", "GCP", "Microservices", "CI/CD", "Remote"
    }
    for j in raw_pool:
        for s in j.get("skills", []):
            if s:
                core_skill_set.add(s)
    
    all_skill_options = sorted(list(core_skill_set))

    col_search1, col_search2, col_btn = st.columns([2.5, 1.6, 0.9], vertical_alignment="bottom")
    with col_search1:
        st.multiselect(
            "Keywords & Tech Stack",
            options=all_skill_options,
            key="selected_skills",
            label_visibility="collapsed"
        )
    with col_search2:
        search_q = st.text_input("Search", placeholder="Search role, company...", label_visibility="collapsed")
    with col_btn:
        st.button("🔍 Check Fit", type="primary", use_container_width=True, key="btn_check_fit")
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    displayed_jobs = scored_jobs
    if search_q:
        q = search_q.lower()
        displayed_jobs = [j for j in scored_jobs if q in j.get("title", "").lower() or q in j.get("company", "").lower()]

    for job in displayed_jobs:
        job_id = job.get("id", "")
        title = job.get("title", "Software Engineer")
        raw_company = job.get("company", "Startup")
        clean_company = re.sub(r'\s*\(\s*YC\s+[^\)]+\)', '', raw_company).strip()
        location = job.get("location", "Remote")
        salary = job.get("salary_str", "$150,000 - $200,000")
        score = job.get("match_score", 0)
        batch = job.get("batch", "YC")
        stage = job.get("stage", "Seed")
        url = job.get("url", "#")
        
        matched_skills = job.get("matched_keywords", [])
        missing_skills = job.get("missing_keywords", [])
        
        matched_html = "".join([f"<span class='micro-badge micro-badge-matched'>{s}</span>" for s in matched_skills])
        missing_html = "".join([f"<span class='micro-badge micro-badge-missing'>{s}</span>" for s in missing_skills])
        
        with st.container(border=True):
            cr1, cr2 = st.columns([4, 1], vertical_alignment="center")
            
            with cr1:
                st.markdown(f"**{title}** <span class='micro-badge match-badge' style='margin-left:8px;'>{score}% Match</span>", unsafe_allow_html=True)
                st.caption(f"{clean_company}")
                
                st.markdown(f"<div><span class='micro-badge'>{batch} • {stage}</span><span class='micro-badge'>{location}</span><span class='micro-badge'>{salary}</span></div>", unsafe_allow_html=True)
                
                st.markdown("<div style='margin-top: 8px; font-size: 0.8rem;'>", unsafe_allow_html=True)
                if matched_html:
                    st.markdown(f"<div style='margin-bottom: 4px;'><b>Matched:</b> {matched_html}</div>", unsafe_allow_html=True)
                if missing_html:
                    st.markdown(f"<div><b>Missing:</b> {missing_html}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with cr2:
                st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
                st.link_button("Apply →", url=url, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            with st.expander("Draft Founder Pitch"):
                pitch_bg = ", ".join(st.session_state["selected_skills"]) or "Software Engineer"
                pitch_data = generate_cold_email_pitch(pitch_bg, job, "Candidate")
                st.code(pitch_data["formatted_email"], language="markdown")

# =============================================================================
# TAB 2: AI PITCH GENERATOR
# =============================================================================
elif active_tab == "pitch-generator":
    st.markdown("### Cold Email Pitch Generator")
    job_titles_map = {f"{j['title']} @ {j['company']}": j for j in scored_jobs}

    c1, c2 = st.columns([3, 1])
    with c1:
        target = st.selectbox("Opportunity", list(job_titles_map.keys()) if job_titles_map else ["None"], label_visibility="collapsed")
    with c2:
        applicant = st.text_input("Name", value="Candidate", label_visibility="collapsed")

    bio = st.text_area("Your Background", value="Senior Engineer building Python & React apps.", height=100)

    if st.button("Generate Pitch", key="btn_gen"):
        if target in job_titles_map:
            job_info = job_titles_map[target]
            res = generate_cold_email_pitch(bio, job_info, applicant)
            with st.container(border=True):
                st.markdown("#### Drafted Pitch")
                st.markdown(res["formatted_email"])


# =============================================================================
# TAB 3: MARKET ANALYTICS
# =============================================================================
elif active_tab == "analytics":
    from analytics import build_salary_by_stage_df, build_top_skills_df
    
    col_chart_left, col_chart_right = st.columns(2)
    
    with col_chart_left:
        st.markdown("#### Top In-Demand Tech Stacks")
        top_skills_df = build_top_skills_df(st.session_state["jobs_data"], top_n=8)
        st.bar_chart(top_skills_df.set_index("Technology"))
        
    with col_chart_right:
        st.markdown("#### Avg Salary by Funding Stage")
        stage_salary_df = build_salary_by_stage_df(st.session_state["jobs_data"])
        st.bar_chart(stage_salary_df.set_index("Stage"))

# =============================================================================
# TAB 4: TERMINAL
# =============================================================================
elif active_tab == "terminal":
    st.markdown("### Bright Data Scraper Terminal")
    
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        with st.container(border=True):
            st.caption("API TOKEN STATUS")
            if env_token:
                st.markdown("### Active / Detected")
                st.caption(f"Masked: `{env_token[:4]}...{env_token[-4:] if len(env_token) > 8 else ''}`")
            else:
                st.markdown("### Missing")
                st.caption("Add `BRIGHT_DATA_API_TOKEN` to your `.env` file.")

    with col_stat2:
        with st.container(border=True):
            st.caption("SCRAPER STATUS")
            st.markdown(f"### Connected to `{DEFAULT_COLLECTOR_ID}`")
            st.caption(f"Target: `{DEFAULT_TARGET_URL}`")

    with st.container(border=True):
        st.markdown("#### Live Collector Diagnostics")
        st.markdown("Verify authentication and cloud endpoint latency with Bright Data Scraper Studio.")
        
        if st.button("Run Live Connection Test", key="btn_run_test", type="primary"):
            if not env_token:
                st.error("Cannot run live test: BRIGHT_DATA_API_TOKEN is not configured.")
            else:
                with st.spinner("Pinging Bright Data DCA endpoint..."):
                    latency, is_ok, msg = test_bright_data_connection(env_token)
                    if is_ok:
                        st.success(f"[SUCCESS] Authenticated & Connected to Bright Data (HTTP 200) - Latency: {latency:.2f}s")
                        st.code(json.dumps({
                            "status": "online",
                            "collector_id": DEFAULT_COLLECTOR_ID,
                            "latency_seconds": round(latency, 3),
                            "target_url": DEFAULT_TARGET_URL,
                            "authenticated": True
                        }, indent=2), language="json")
                    else:
                        st.error(f"[ERROR] {msg}")

        st.markdown("---")
        st.markdown("#### Scraper Specifications")
        st.code(f"""Collector ID: {DEFAULT_COLLECTOR_ID}
Target Job Board: {DEFAULT_TARGET_URL}
Trigger Endpoint: https://api.brightdata.com/dca/trigger?collector={DEFAULT_COLLECTOR_ID}&queue_next=1
Dataset Endpoint: https://api.brightdata.com/dca/dataset?id={{COLLECTION_ID}}
Auth Header: Authorization: Bearer <TOKEN>""", language="yaml")
