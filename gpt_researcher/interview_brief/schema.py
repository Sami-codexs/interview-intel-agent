"""Structured output schema for the Interview-Intel Agent.

This module defines the Pydantic model that serves as the contract
for all downstream pipeline stages. Every component that produces or
consumes an interview brief must validate against InterviewBrief.
"""

from typing import List
from pydantic import BaseModel, Field


class InterviewBrief(BaseModel):
    """Structured interview preparation brief for a given company.

    All fields default to empty lists so the pipeline never returns
    None / null for a missing value — it returns an empty list, which
    makes downstream consumption predictable.
    """

    company: str = Field(
        ...,
        description="The company name the brief is about."
    )
    interview_rounds: List[str] = Field(
        default_factory=list,
        description=(
            "Ordered list of interview rounds reported by candidates, e.g. "
            "'Online Assessment', 'Technical Round 1', 'System Design', 'HR Round'."
        ),
    )
    common_topics: List[str] = Field(
        default_factory=list,
        description=(
            "DSA patterns, system-design areas, or behavioural themes "
            "commonly reported for this company."
        ),
    )
    tech_stack: List[str] = Field(
        default_factory=list,
        description=(
            "Languages, frameworks, and infrastructure tools the company "
            "actually uses (sourced from GitHub, engineering blogs, etc.)."
        ),
    )
    talking_points: List[str] = Field(
        default_factory=list,
        description=(
            "2-4 concise culture-fit / 'why this company' notes that "
            "can be dropped into an interview conversation."
        ),
    )
    sources: List[str] = Field(
        default_factory=list,
        description="URLs used to build the brief, for transparency and citation."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "company": "Amazon",
                "interview_rounds": [
                    "Online Assessment (OA)",
                    "Phone Screen",
                    "Virtual Onsite – 4 loops"
                ],
                "common_topics": [
                    "Leadership Principles (STAR format)",
                    "System Design at scale",
                    "LP-solvable graph problems"
                ],
                "tech_stack": ["Java", "AWS", "DynamoDB", "Kotlin"],
                "talking_points": [
                    "Amazon's Leadership Principles are evaluated in every round.",
                    "Customer obsession is the #1 cultural pillar."
                ],
                "sources": [
                    "https://www.glassdoor.com/...",
                    "https://github.com/amazon/..."
                ]
            }
        }