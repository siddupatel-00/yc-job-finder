"""
AI Cold Email & Application Pitch Generator
============================================
Generates personalized, high-converting 1-paragraph cold email pitches
tailored directly to startup founders and engineering hiring managers.
"""

from typing import Dict, Any, List


def generate_cold_email_pitch(
    candidate_background: str,
    job: Dict[str, Any],
    candidate_name: str = "Candidate"
) -> Dict[str, str]:
    """
    Synthesizes candidate background and job requirements into a punchy,
    Y Combinator-style 1-paragraph cold application email.

    Args:
        candidate_background: Raw bio or key strengths of the applicant.
        job: Target job dictionary.
        candidate_name: Optional name for email signoff.

    Returns:
        Dictionary with 'subject', 'body', 'key_highlights', and 'formatted_email'.
    """
    company = job.get("company", "the startup")
    title = job.get("title", "Engineering Role")
    batch = job.get("batch", "YC")
    skills = job.get("skills", [])
    location = job.get("location", "Remote")
    
    top_stack = ", ".join(skills[:3]) if skills else "modern distributed systems"
    
    # Subject lines
    subject = f"{title} // {candidate_name} ({batch} applicant)"

    # Opening Hook
    if candidate_background.strip():
        bg_summary = candidate_background.strip().replace("\n", " ")
        if len(bg_summary) > 180:
            bg_summary = bg_summary[:180] + "..."
    else:
        bg_summary = f"builder with hands-on expertise across {top_stack}"

    # 1-Paragraph Cold Email Body
    body = (
        f"Hi {company} team,\n\n"
        f"I’ve been following {company}’s momentum out of {batch} and wanted to reach out regarding the {title} opening. "
        f"As a {bg_summary}, I specialize in shipping high-throughput workflows and deep technical craft in {top_stack}. "
        f"Given your focus on solving core product bottlenecks in {skills[0] if skills else 'engineering'}, I’m confident I can contribute from day one and thrive in your high-autonomy team.\n\n"
        f"Would love to jump on a quick 15-minute intro call this week to discuss how I can help accelerate {company}'s roadmap.\n\n"
        f"Best,\n{candidate_name}"
    )

    # Key highlights
    highlights = [
        f"**Stack Synergy**: Proven proficiency matching {company}'s core stack ({top_stack}).",
        f"**Velocity First**: High-speed shipping culture, ideal for {batch} startup pacing.",
        f"**Location Fit**: Available immediately for {location}."
    ]

    return {
        "subject": subject,
        "body": body,
        "key_highlights": "\n".join([f"• {h}" for h in highlights]),
        "formatted_email": f"**Subject:** `{subject}`\n\n```text\n{body}\n```"
    }
