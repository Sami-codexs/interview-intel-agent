"""Interview-Intel Agent orchestration.

This module wires the interview-specific prompts and schema into the existing
GPTResearcher planner → executor → publisher flow without replacing it.
"""

import json
import logging
import os
import re
from typing import List, Dict, Any

from gpt_researcher import GPTResearcher
from gpt_researcher.config import Config
from gpt_researcher.utils.llm import create_chat_completion
from gpt_researcher.utils.enum import Tone, ReportSource

from .schema import InterviewBrief
from .prompts import (
    interview_agent_role_prompt,
    generate_interview_queries_prompt,
    synthesize_interview_brief_prompt,
)

logger = logging.getLogger(__name__)


async def run_interview_research(
    company: str,
    config_path: str | None = None,
    headers: dict | None = None,
    verbose: bool = True,
) -> InterviewBrief:
    """Run end-to-end interview-intelligence research for a company.

    Reuses GPTResearcher for search + context gathering, then applies a
    domain-specific synthesis prompt to produce a structured InterviewBrief.
    """
    headers = headers or {}
    company = company.strip()

    # 1. Generate targeted sub-queries (cheap/fast LLM call)
    cfg = Config(config_path)
    sub_queries_prompt = generate_interview_queries_prompt(company)

    try:
        sub_queries_raw = await create_chat_completion(
            model=cfg.fast_llm_model,
            messages=[
                {"role": "system", "content": interview_agent_role_prompt()},
                {"role": "user", "content": sub_queries_prompt},
            ],
            llm_provider=cfg.fast_llm_provider,
            temperature=0.2,
            max_tokens=800,
            llm_kwargs=cfg.llm_kwargs,
        )
        sub_queries = json.loads(sub_queries_raw)
        if not isinstance(sub_queries, list):
            sub_queries = []
    except Exception as e:
        logger.warning(f"Failed to generate sub-queries: {e}. Falling back to defaults.")
        sub_queries = [
            f"{company} software engineer interview process experience",
            f"{company} engineering blog tech stack",
            f"{company} leetcode interview questions",
        ]

    logger.info(f"Interview sub-queries for {company}: {sub_queries}")

    # 2. Run GPTResearcher for broad web research
    main_query = f"Interview process, common questions, and engineering culture at {company}"

    researcher = GPTResearcher(
        query=main_query,
        report_type="research_report",
        report_source=ReportSource.Web.value,
        tone=Tone.Objective,
        config_path=config_path,
        headers=headers,
        agent="Interview Intelligence Agent",
        role=interview_agent_role_prompt(),
        verbose=verbose,
    )

    await researcher.conduct_research()
    web_context = researcher.context
    visited_urls = list(researcher.visited_urls)

    if isinstance(web_context, list):
        web_context = "\n\n".join(str(c) for c in web_context)
    else:
        web_context = str(web_context)

    # 3. Gather GitHub tech-stack context (if GitHub retriever is enabled)
    github_context = ""
    try:
        from gpt_researcher.actions.retriever import get_retriever
        from gpt_researcher.actions.query_processing import get_search_results

        github_cls = get_retriever("github")
        if github_cls:
            gh_results = await get_search_results(
                query=company,
                retriever=github_cls,
                query_domains=None,
            )
            if gh_results:
                github_context = "\n\n".join(
                    f"Repo: {r.get('title', 'N/A')}\n{r.get('body', '')}"
                    for r in gh_results
                )
                visited_urls.extend([r.get("href", "") for r in gh_results if r.get("href")])
    except Exception as e:
        logger.warning(f"GitHub retriever failed or not configured: {e}")

    # 4. Combine raw findings — TRUNCATED for free-tier token limits
    MAX_WEB_CHARS = 8000
    MAX_GH_CHARS = 2000

    if len(web_context) > MAX_WEB_CHARS:
        web_context = web_context[:MAX_WEB_CHARS] + "\n...[truncated]"
    if len(github_context) > MAX_GH_CHARS:
        github_context = github_context[:MAX_GH_CHARS] + "\n...[truncated]"

    raw_findings = f"""WEB RESEARCH CONTEXT:
{web_context}

GITHUB / OPEN-SOURCE CONTEXT:
{github_context}

SUB-QUERIES USED:
{chr(10).join(f"- {q}" for q in sub_queries)}
"""

    # 5. Synthesize structured InterviewBrief (smart LLM)
    synthesis_prompt = synthesize_interview_brief_prompt(company, raw_findings)

    synthesis_raw = await create_chat_completion(
        model=cfg.smart_llm_model,
        messages=[
            {"role": "system", "content": interview_agent_role_prompt()},
            {"role": "user", "content": synthesis_prompt},
        ],
        llm_provider=cfg.smart_llm_provider,
        temperature=0.3,
        max_tokens=2000,
        llm_kwargs=cfg.llm_kwargs,
    )

    # Parse JSON response
    try:
        brief_dict = json.loads(synthesis_raw)
    except json.JSONDecodeError:
        json_match = re.search(r"\{.*\}", synthesis_raw, re.DOTALL)
        if json_match:
            brief_dict = json.loads(json_match.group(0))
        else:
            raise RuntimeError(f"Could not parse synthesis response as JSON: {synthesis_raw[:500]}")

    brief_dict["company"] = company
    brief_dict["sources"] = list(dict.fromkeys([u for u in visited_urls if u]))

    brief = InterviewBrief(**brief_dict)

    logger.info(
        f"InterviewBrief for {company}: "
        f"{len(brief.interview_rounds)} rounds, "
        f"{len(brief.common_topics)} topics, "
        f"{len(brief.tech_stack)} tech items, "
        f"{len(brief.talking_points)} talking points, "
        f"{len(brief.sources)} sources"
    )

    return brief