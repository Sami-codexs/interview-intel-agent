# Interview-Intel Agent

&gt; A domain-specific autonomous research agent built on [GPT Researcher](https://github.com/assafelovic/gpt-researcher) that generates structured, citation-backed interview prep briefs for any company.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## What It Does

Given a company name (e.g. `Amazon`), the agent autonomously:

1. **Plans** targeted sub-queries for interview experiences, engineering blogs, and tech stacks
2. **Researches** the web via Tavily + scrapes real candidate experiences
3. **Discovers** the company's actual tech stack via a custom GitHub REST API retriever
4. **Ranks** sources by credibility (Glassdoor, LeetCode, Blind &gt; generic blogs)
5. **Synthesizes** a structured `InterviewBrief` with rounds, topics, tech stack, talking points, and citations

---

## Architecture
