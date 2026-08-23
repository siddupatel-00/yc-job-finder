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
bg_tertiary = "#121214" if is_dark else "#f1f3f5"
text_primary = "#ededed" if is_dark else "#11181c"
text_secondary = "#a1a1aa" if is_dark else "#687076"
border_color = "#27272a" if is_dark else "#dee2e6"
border_hover = "#3f3f46" if is_dark else "#ced4da"
btn_primary_bg = "#ffffff" if is_dark else "#11181c"
btn_primary_text = "#000000" if is_dark else "#ffffff"

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
    
    /* Multiselect Tags */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {{
        background-color: {bg_tertiary} !important;
        color: {text_primary} !important;
        border: 1px solid {border_color} !important;
        border-radius: 4px !important;
    }}
    [data-testid="stMultiSelect"] [data-baseweb="tag"] span {{
        color: {text_primary} !important;
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
    [data-testid="stVerticalBlockBorderWrapper"] * {{
        color: {text_primary} !important;
    }}
    [data-testid="stVerticalBlockBorderWrapper"] .stCaption, 
    [data-testid="stVerticalBlockBorderWrapper"] .stCaption * {{
        color: {text_secondary} !important;
    }}

    /* Tabs Strict Monochrome Fix */
    button[data-baseweb="tab"] {{
        background: transparent !important;
        color: {text_secondary} !important;
        font-weight: 500 !important;
        border: none !important;
    }}
    button[data-baseweb="tab"] * {{
        color: {text_secondary} !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {text_primary} !important;
        border-bottom: 2px solid {text_primary} !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] * {{
        color: {text_primary} !important;
    }}
    button[data-baseweb="tab"]:hover, 
    button[data-baseweb="tab"]:hover * {{
        color: {text_primary} !important;
    }}
    button[data-baseweb="tab"]:focus,
    button[data-baseweb="tab"]:focus * {{
        color: {text_primary} !important;
    }}
    div[data-baseweb="tab-highlight"] {{
        background-color: {text_primary} !important;
    }}
    div[data-baseweb="tab-border"] {{
        background-color: {border_color} !important;
    }}
    
    div[data-baseweb="tab-list"] {{
        border-bottom: 1px solid {border_color} !important;
        margin-bottom: 24px !important;
    }}

    /* Primary Buttons (Crisp White/Black) */
    .stButton > button[kind="primary"], div.top-cta-btn .stButton > button {{
        background-color: {btn_primary_bg} !important;
        color: {btn_primary_text} !important;
        border: 1px solid {btn_primary_bg} !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
    }}
    .stButton > button[kind="primary"] *, div.top-cta-btn .stButton > button * {{
        color: {btn_primary_text} !important;
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

    /* Link Buttons */
    div[data-testid="stLinkButton"] > a {{
        background-color: {btn_primary_bg} !important;
        color: {btn_primary_text} !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        text-decoration: none !important;
    }}

    /* Micro Badges */
    .micro-badge {{
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        background: {bg_tertiary} !important;
        color: {text_primary} !important;
        border: 1px solid {border_color};
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 8px;
        margin-top: 4px;
        margin-bottom: 4px;
    }}
    
    .match-badge {{
        color: {btn_primary_text} !important;
        background-color: {btn_primary_bg} !important;
        border-color: {btn_primary_bg} !important;
    }}

    
    .micro-badge-matched {{
        background: {text_primary} !important;
        color: {bg_primary} !important;
        border-color: {text_primary} !important;
    }}
    .micro-badge-missing {{
        opacity: 0.6;
    }}

    
    /* URL-routed Segmented Navigation Tabs */
    div[data-testid="stRadio"] {
        border-bottom: 1px solid {border_color} !important;
        margin-bottom: 20px !important;
        padding-bottom: 4px !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        gap: 2rem !important;
        background: transparent !important;
    }
    div[data-testid="stRadio"] label {
        background: transparent !important;
        border: none !important;
        padding: 0 0 8px 0 !important;
        cursor: pointer !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        color: {text_secondary} !important;
        margin-bottom: -5px !important;
    }
    div[data-testid="stRadio"] label:hover,
    div[data-testid="stRadio"] label:hover * {
        color: {text_primary} !important;
    }
    div[data-testid="stRadio"] label > div:first-child {
        display: none !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        color: {text_primary} !important;
        border-bottom: 2px solid {text_primary} !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] * {
        color: {text_primary} !important;
        font-weight: 600 !important;
    }

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
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

TAB_KEYS = ["opportunities", "pitch-generator", "analytics", "terminal"]
TAB_LABELS = {
    "opportunities": f"Opportunities ({len(scored_jobs)})",
    "pitch-generator": "Pitch Generator",
    "analytics": "Analytics",
    "terminal": "Terminal"
}

# Read current active tab from URL query params
current_tab_param = st.query_params.get("tab", "opportunities")
if current_tab_param not in TAB_KEYS:
    current_tab_param = "opportunities"

def handle_tab_change():
    st.query_params["tab"] = st.session_state["url_nav_tab"]

active_tab = st.radio(
    "Navigation Tabs",
    options=TAB_KEYS,
    format_func=lambda k: TAB_LABELS[k],
    index=TAB_KEYS.index(current_tab_param),
    horizontal=True,
    label_visibility="collapsed",
    key="url_nav_tab",
    on_change=handle_tab_change
)

# Ensure query params stay synced
if st.query_params.get("tab") != active_tab:
    st.query_params["tab"] = active_tab

# =============================================================================
# TAB 1: OPPORTUNITIES
# =============================================================================
if active_tab == "opportunities":
    col_search1, col_search2 = st.columns([2, 1])
    with col_search1:
        st.session_state["selected_skills"] = st.multiselect(
            "Keywords",
            ["Python", "AI", "React", "TypeScript", "Node", "Go", "Rust", "Remote"],
            default=st.session_state["selected_skills"],
            label_visibility="collapsed"
        )
    with col_search2:
        search_q = st.text_input("Search", placeholder="Role, company...", label_visibility="collapsed")
    
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
    with st.container(border=True):
        st.markdown("#### Scraper Config")
        st.code(f"Collector ID: {DEFAULT_COLLECTOR_ID}\nTarget URL: {DEFAULT_TARGET_URL}", language="yaml")
