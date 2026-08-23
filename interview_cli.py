#!/usr/bin/env python3
"""Standalone CLI for the Interview-Intel Agent.

Usage:
    python interview_cli.py --company "Amazon"
    python interview_cli.py --company "Stripe" --output-dir ./output
"""

import argparse
import asyncio
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpt_researcher.interview_brief import run_interview_research, InterviewBrief


def format_brief(brief: InterviewBrief) -> str:
    """Render an InterviewBrief as readable formatted text."""
    lines = [
        f"# Interview Prep Brief: {brief.company}",
        f"Generated: {datetime.utcnow().isoformat()}Z",
        "",
        "## Interview Rounds",
    ]
    for r in brief.interview_rounds or []:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("## Common Topics")
    for t in brief.common_topics or []:
        lines.append(f"- {t}")
    lines.append("")
    lines.append("## Tech Stack")
    for t in brief.tech_stack or []:
        lines.append(f"- {t}")
    lines.append("")
    lines.append("## Talking Points")
    for tp in brief.talking_points or []:
        lines.append(f"- {tp}")
    lines.append("")
    lines.append("## Sources")
    for s in brief.sources or []:
        lines.append(f"- {s}")
    lines.append("")
    return "\n".join(lines)


def write_markdown(brief: InterviewBrief, output_dir: str) -> str:
    """Write the brief to a markdown file and return the path."""
    os.makedirs(output_dir, exist_ok=True)
    safe_name = brief.company.lower().replace(" ", "_")
    filename = f"{safe_name}_interview_brief.md"
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(format_brief(brief))
    return path


async def main():
    parser = argparse.ArgumentParser(
        description="Interview-Intel Agent — autonomous interview-prep research"
    )
    parser.add_argument("--company", required=True, help="Company name to research")
    parser.add_argument("--output-dir", default="output", help="Directory for markdown output")
    parser.add_argument("--config", default=None, help="Optional GPTResearcher JSON config path")
    parser.add_argument("--verbose", action="store_true", default=True, help="Stream progress logs")
    args = parser.parse_args()

    print(f"🔍 Starting interview-intel research for: {args.company}")
    start = time.time()

    brief = await run_interview_research(
        company=args.company,
        config_path=args.config,
        verbose=args.verbose,
    )

    elapsed = time.time() - start
    print(f"\n✅ Research complete in {elapsed:.1f}s")
    print(format_brief(brief))

    md_path = write_markdown(brief, args.output_dir)
    print(f"\n📝 Markdown brief written to: {md_path}")


if __name__ == "__main__":
    asyncio.run(main())