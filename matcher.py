"""
AI Job Matching & YC Market Intelligence Engine
===============================================
Multi-factor candidate ranking, semantic resume profile extraction,
startup pitch generator, and market analytics aggregator.
"""

import re
from typing import List, Dict, Any, Tuple, Set
from collections import Counter

# Core tech lexicon for semantic parsing
COMMON_TECH_LEXICON: List[str] = [
    "python", "react", "typescript", "javascript", "pytorch", "llms", "rag",
    "fastapi", "vectordb", "docker", "kubernetes", "aws", "gcp", "rust", "go",
    "golang", "c++", "next.js", "graphql", "sql", "postgresql", "mongodb",
    "kafka", "redis", "terraform", "devops", "linux", "distributed systems",
    "tailwind", "tailwindcss", "nlp", "computer vision", "cuda", "simd",
    "microservices", "snowflake", "dbt", "ios", "swift", "react native"
]


def clean_keyword(kw: str) -> str:
    """Normalize a keyword token for case-insensitive matching."""
    return kw.strip().lower()


def parse_keywords(keywords_input: Any) -> List[str]:
    """
    Parse comma-separated string, list, or set into a deduplicated list of tokens.

    Args:
        keywords_input: Raw string or iterable of keywords.

    Returns:
        Deduplicated list of cleaned keyword strings.
    """
    if isinstance(keywords_input, str):
        tokens = [k.strip() for k in re.split(r"[,|\n/]+", keywords_input) if k.strip()]
    elif isinstance(keywords_input, (list, set, tuple)):
        tokens = [str(k).strip() for k in keywords_input if str(k).strip()]
    else:
        tokens = []

    seen: Set[str] = set()
    deduped: List[str] = []
    for t in tokens:
        cleaned = clean_keyword(t)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            deduped.append(t)
    return deduped


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract recognized tech stack skills from free-form candidate resume or bio.

    Args:
        text: Free-text bio or Markdown resume string.

    Returns:
        Alphabetically sorted list of properly capitalized detected skills.
    """
    if not text:
        return []

    text_lower = text.lower()
    detected = []

    for tech in COMMON_TECH_LEXICON:
        pattern = r"\b" + re.escape(tech) + r"\b"
        if re.search(pattern, text_lower):
            # Normalize proper casing
            proper = tech.title()
            if tech in ["llms", "rag", "vectordb", "aws", "gcp", "sql", "nlp", "cuda", "simd", "ios"]:
                proper = tech.upper()
            elif tech == "next.js":
                proper = "Next.js"
            elif tech == "fastapi":
                proper = "FastAPI"
            elif tech == "c++":
                proper = "C++"
            elif tech == "react native":
                proper = "React Native"
            detected.append(proper)

    return sorted(list(set(detected)))


def calculate_job_score(
    job: Dict[str, Any],
    target_keywords: List[str],
    preferred_location: str = "Any",
    stage_filter: str = "Any",
    visa_only: bool = False
) -> Dict[str, Any]:
    """
    Compute multi-factor relevance fit score (0 - 100%).

    Weights:
    - Target Skills / Tech Stack Match: 45%
    - Title Match: 25%
    - Description Deep Scan: 15%
    - Location Compatibility: 10%
    - Baseline Floor: 5%

    Args:
        job: Dictionary representing a single job opportunity.
        target_keywords: List of target candidate skill keywords.
        preferred_location: Desired location filter.
        stage_filter: Company funding stage filter.
        visa_only: Boolean flag requiring visa sponsorship.

    Returns:
        Updated job dictionary containing match_score, matched_keywords, and score_grade.
    """
    if not target_keywords:
        return {
            **job,
            "match_score": 100,
            "matched_keywords": [],
            "missing_keywords": [],
            "score_grade": "General Listing",
            "fit_tier": "Full Pool"
        }

    job_title = (job.get("title") or "").lower()
    job_desc = (job.get("description") or "").lower()
    job_loc = (job.get("location") or "").lower()
    job_work_type = (job.get("work_type") or "").lower()
    job_skills = [str(s).lower() for s in job.get("skills", [])]

    matched_keywords: Set[str] = set()
    skills_matches = 0
    title_matches = 0
    desc_matches = 0

    total_keywords_count = len(target_keywords)

    for kw in target_keywords:
        kw_clean = clean_keyword(kw)
        if not kw_clean:
            continue

        pattern = r"\b" + re.escape(kw_clean) + r"\b"

        # Skills match
        if any(kw_clean in s or s in kw_clean for s in job_skills):
            matched_keywords.add(kw)
            skills_matches += 1

        # Title match
        if bool(re.search(pattern, job_title)) or (kw_clean in job_title):
            matched_keywords.add(kw)
            title_matches += 1

        # Description match
        if bool(re.search(pattern, job_desc)) or (kw_clean in job_desc):
            matched_keywords.add(kw)
            desc_matches += 1

    # Location scoring
    loc_score = 0.4
    pref_loc_clean = preferred_location.strip().lower()
    if pref_loc_clean == "any" or not pref_loc_clean:
        loc_score = 1.0
    elif "remote" in pref_loc_clean and ("remote" in job_loc or "remote" in job_work_type):
        loc_score = 1.0
        matched_keywords.add("Remote")
    elif pref_loc_clean in job_loc:
        loc_score = 1.0
        matched_keywords.add(preferred_location)

    # Calculate weighted sub-scores
    skill_sub = (skills_matches / total_keywords_count) if total_keywords_count else 0
    title_sub = (title_matches / total_keywords_count) if total_keywords_count else 0
    desc_sub = (desc_matches / total_keywords_count) if total_keywords_count else 0

    raw_score = (
        (skill_sub * 45.0) +
        (title_sub * 25.0) +
        (desc_sub * 15.0) +
        (loc_score * 10.0) +
        5.0
    )

    # Coverage boost
    coverage = len(matched_keywords) / total_keywords_count if total_keywords_count else 0
    if coverage >= 0.7:
        raw_score = min(100.0, raw_score * 1.2)
    elif coverage == 0:
        raw_score = max(0.0, raw_score * 0.25)

    final_score = int(round(min(100.0, max(0.0, raw_score))))

    # Fit Grade Classification
    if final_score >= 80:
        grade = "Top Tier Fit"
    elif final_score >= 60:
        grade = "Strong Fit"
    elif final_score >= 40:
        grade = "Moderate Fit"
    else:
        grade = "Adjacent Fit"

    missing = [kw for kw in target_keywords if kw not in matched_keywords and kw.lower() != "remote"]

    return {
        **job,
        "match_score": final_score,
        "matched_keywords": sorted(list(matched_keywords)),
        "missing_keywords": missing,
        "score_grade": grade,
        "coverage_pct": int(round(coverage * 100))
    }


def rank_and_filter_jobs(
    jobs: List[Dict[str, Any]],
    target_keywords: List[str],
    preferred_location: str = "Any",
    stage_filter: str = "Any",
    visa_only: bool = False,
    min_score: int = 0,
    search_query: str = ""
) -> List[Dict[str, Any]]:
    """
    Score, filter, and rank job listings in descending order of relevance.

    Returns:
        Ranked list of job dictionaries.
    """
    scored_jobs = []

    for job in jobs:
        scored = calculate_job_score(job, target_keywords, preferred_location, stage_filter, visa_only)

        if scored["match_score"] < min_score:
            continue

        if preferred_location != "Any":
            pref = preferred_location.lower()
            job_loc = (job.get("location") or "").lower()
            job_type = (job.get("work_type") or "").lower()
            if pref == "remote only" and "remote" not in job_loc and "remote" not in job_type:
                continue

        if stage_filter != "Any":
            job_stage = (job.get("stage") or "").lower()
            if stage_filter.lower() not in job_stage:
                continue

        if visa_only and not job.get("visa_sponsorship", False):
            continue

        if search_query.strip():
            sq = search_query.strip().lower()
            title = (job.get("title") or "").lower()
            company = (job.get("company") or "").lower()
            desc = (job.get("description") or "").lower()
            skills = " ".join([str(s).lower() for s in job.get("skills", [])])
            if sq not in title and sq not in company and sq not in desc and sq not in skills:
                continue

        scored_jobs.append(scored)

    scored_jobs.sort(key=lambda x: (x["match_score"], len(x["matched_keywords"])), reverse=True)
    return scored_jobs


def match_by_resume(resume_text: str, jobs: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Parse candidate resume, extract skills, and rank jobs against the candidate profile.

    Returns:
        (detected_skills_list, ranked_jobs_list)
    """
    detected_skills = extract_skills_from_text(resume_text)
    ranked_jobs = rank_and_filter_jobs(jobs, detected_skills, min_score=15)
    return detected_skills, ranked_jobs


def generate_tailored_pitch(candidate_skills: List[str], job: Dict[str, Any]) -> List[str]:
    """
    Generate 3 impactful bullet points highlighting how candidate skills solve the startup's mission.

    Returns:
        List of 3 application pitch bullet points.
    """
    company = job.get("company", "this startup")
    title = job.get("title", "Engineering Role")
    job_skills = job.get("skills", [])

    overlap = [s for s in candidate_skills if any(s.lower() == js.lower() for js in job_skills)]
    top_skills_str = ", ".join(overlap[:3]) if overlap else ", ".join(candidate_skills[:3])

    return [
        f"**Immediate Velocity**: Hands-on proficiency in {top_skills_str or 'core systems'}, ready to ship features immediately for {company}'s {title} role.",
        f"**Architectural Alignment**: Direct experience scaling workflows matching {company}'s stack in {' & '.join(job_skills[:2]) if job_skills else 'distributed systems'}.",
        f"**Founder Mindset**: High-autonomy problem solver eager to tackle core product challenges and drive rapid customer impact at {company}."
    ]


def compute_market_insights(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate telemetry analytics across current job listings.

    Returns:
        Dictionary containing top_skills, avg salaries, remote ratio, and stage distribution.
    """
    if not jobs:
        return {
            "top_skills": [],
            "avg_salary_min": 0,
            "avg_salary_max": 0,
            "remote_ratio": 0,
            "visa_ratio": 0,
            "stages": {}
        }

    all_skills = []
    min_salaries = []
    max_salaries = []
    remote_count = 0
    visa_count = 0
    stages_counter = Counter()

    for j in jobs:
        for s in j.get("skills", []):
            all_skills.append(s)

        s_min = j.get("salary_min")
        s_max = j.get("salary_max")
        if s_min:
            min_salaries.append(s_min)
        if s_max:
            max_salaries.append(s_max)

        loc = (j.get("location") or "") + " " + (j.get("work_type") or "")
        if "remote" in loc.lower():
            remote_count += 1

        if j.get("visa_sponsorship", False):
            visa_count += 1

        stage = j.get("stage", "Seed")
        stage_clean = "Seed" if "seed" in stage.lower() else ("Series A" if "series a" in stage.lower() else "Growth / Other")
        stages_counter[stage_clean] += 1

    skill_counts = Counter(all_skills).most_common(8)
    avg_min = int(sum(min_salaries) / len(min_salaries)) if min_salaries else 150000
    avg_max = int(sum(max_salaries) / len(max_salaries)) if max_salaries else 210000
    remote_pct = int(round((remote_count / len(jobs)) * 100)) if jobs else 0
    visa_pct = int(round((visa_count / len(jobs)) * 100)) if jobs else 0

    return {
        "top_skills": skill_counts,
        "avg_salary_min": avg_min,
        "avg_salary_max": avg_max,
        "remote_ratio": remote_pct,
        "visa_ratio": visa_pct,
        "stages": dict(stages_counter)
    }
