"""Domain-specific prompts for the Interview-Intel Agent.

These prompts live in a separate module so the original generic-research
prompts in gpt_researcher/prompts.py remain untouched and available.
"""

from datetime import datetime, timezone


def interview_agent_role_prompt() -> str:
    """Defines the agent's persona as an interview-prep researcher."""
    return (
        "You are an elite interview-intelligence researcher. Your sole purpose is to "
        "help software-engineering candidates prepare for interviews at specific companies. "
        "You hunt down real interview experiences, engineering-culture signals, and "
        "verified tech-stack data. You never hallucinate rounds, topics, or tools. "
        "If you cannot find evidence for a claim, you leave the field empty. "
        "You cite every source you use."
    )


def generate_interview_queries_prompt(company: str) -> str:
    """Generate 3-5 targeted sub-queries for interview research."""
    return f"""You are an interview-intelligence researcher.

Your task is to generate 3-5 targeted search queries that will help a software-engineering
candidate prepare for interviews at **{company}**.

Each query must be a plain natural language phrase. Do not use search operators
such as site:, filetype:, inurl:, OR, AND, or NOT.

Target these information categories:
1. Interview experience / process (Glassdoor, LeetCode Discuss, Blind, Reddit)
2. Engineering blog / technical culture (company engineering blog, Medium)
3. Tech stack and open-source footprint (GitHub org, popular repos)
4. Recent hiring trends or interview format changes (news, forums)
5. Specific DSA / system-design topics frequently asked

Assume the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')}.

You must respond with a JSON list of strings in this exact format:
["query 1", "query 2", "query 3", ...]
The response should contain ONLY the JSON list — no markdown fences, no extra text.
"""


def synthesize_interview_brief_prompt(company: str, raw_findings: str) -> str:
    """Instruct the LLM to return JSON matching InterviewBrief exactly."""
    return f"""You are an interview-intelligence researcher.

COMPANY: {company}

RAW FINDINGS:
{raw_findings}

---

TASK: Synthesize the raw findings into a structured JSON object that matches the
InterviewBrief schema exactly.

The JSON must have these keys and value types:
- "company": string (the company name)
- "interview_rounds": list of strings — ordered rounds reported by candidates.
- "common_topics": list of strings — DSA patterns, system-design areas, or behavioural themes commonly reported.
- "tech_stack": list of strings — languages, frameworks, and tools the company actually uses.
- "talking_points": list of strings — 2-4 concise "why this company" / culture-fit notes.
- "sources": list of strings — URLs you actually used from the raw findings.

CRITICAL RULES:
1. If no evidence exists for a field, return an empty list [] for that field. NEVER hallucinate.
2. Only include information that is explicitly supported by the raw findings.
3. Deduplicate items — do not list "Python" three times.
4. Keep talking_points to 2-4 bullets, each under 20 words.
5. Return ONLY valid JSON. No markdown fences, no extra commentary.
"""