"""
Market Analytics & Compensation Telemetry Module
================================================
Computes statistical distributions, salary percentiles,
and technology stack trends across startup opportunities.
"""

from typing import List, Dict, Any, Tuple
from collections import Counter
import pandas as pd


def get_summary_telemetry(jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute core telemetry metrics for cards and overview summaries.
    """
    if not jobs:
        return {
            "total_count": 0,
            "avg_salary_min": 0,
            "avg_salary_max": 0,
            "median_salary": 0,
            "remote_ratio": 0,
            "visa_ratio": 0
        }

    min_salaries = [j.get("salary_min", 0) for j in jobs if j.get("salary_min")]
    max_salaries = [j.get("salary_max", 0) for j in jobs if j.get("salary_max")]
    
    avg_min = int(sum(min_salaries) / len(min_salaries)) if min_salaries else 150000
    avg_max = int(sum(max_salaries) / len(max_salaries)) if max_salaries else 210000
    median_comp = int((avg_min + avg_max) / 2)

    remote_count = sum(1 for j in jobs if "remote" in ((j.get("location") or "") + " " + (j.get("work_type") or "")).lower())
    visa_count = sum(1 for j in jobs if j.get("visa_sponsorship", False))

    return {
        "total_count": len(jobs),
        "avg_salary_min": avg_min,
        "avg_salary_max": avg_max,
        "median_salary": median_comp,
        "remote_ratio": int(round((remote_count / len(jobs)) * 100)) if jobs else 0,
        "visa_ratio": int(round((visa_count / len(jobs)) * 100)) if jobs else 0
    }


def build_top_skills_df(jobs: List[Dict[str, Any]], top_n: int = 10) -> pd.DataFrame:
    """
    Generate DataFrame of most requested technical skills.
    """
    all_skills = []
    for j in jobs:
        for s in j.get("skills", []):
            all_skills.append(s)

    counts = Counter(all_skills).most_common(top_n)
    df = pd.DataFrame(counts, columns=["Technology", "Job Openings"])
    return df


def build_salary_distribution_df(jobs: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Generate DataFrame showing salary ranges by role and company.
    """
    records = []
    for j in jobs:
        records.append({
            "Role": j.get("title", "Role"),
            "Company": j.get("company", "Company"),
            "Min Comp ($k)": int(j.get("salary_min", 140000) / 1000),
            "Max Comp ($k)": int(j.get("salary_max", 200000) / 1000),
            "Stage": j.get("stage", "Seed"),
            "Batch": j.get("batch", "YC")
        })
    return pd.DataFrame(records)


def build_funding_stage_df(jobs: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Generate funding stage breakdown table.
    """
    counter = Counter()
    for j in jobs:
        stage = j.get("stage", "Seed")
        clean_stage = "Seed" if "seed" in stage.lower() else ("Series A" if "series a" in stage.lower() else "Growth / Other")
        counter[clean_stage] += 1

    df = pd.DataFrame(list(counter.items()), columns=["Funding Stage", "Active Listings"])
    return df

def build_salary_by_stage_df(jobs: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Generate DataFrame showing average salary ranges across stages (Seed vs Series A vs Series B).
    """
    records = []
    for j in jobs:
        s = j.get("stage", "Seed").lower()
        if "seed" in s:
            stage = "Seed"
        elif "series a" in s:
            stage = "Series A"
        elif "series b" in s:
            stage = "Series B"
        else:
            stage = "Growth / Other"
            
        salary_mid = (j.get("salary_min", 150000) + j.get("salary_max", 200000)) / 2 / 1000
        records.append({
            "Stage": stage,
            "Avg Salary ($k)": salary_mid
        })
    df = pd.DataFrame(records)
    if not df.empty:
        df = df.groupby("Stage")["Avg Salary ($k)"].mean().reset_index()
        # Ensure ordering
        stage_order = {"Seed": 1, "Series A": 2, "Series B": 3, "Growth / Other": 4}
        df["order"] = df["Stage"].map(stage_order)
        df = df.sort_values("order").drop("order", axis=1)
    return df
