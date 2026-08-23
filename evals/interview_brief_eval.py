#!/usr/bin/env python3
"""Minimal evaluation script for the Interview-Intel Agent.

Runs run_interview_research against 5 real companies and prints:
- Whether all schema fields were populated
- Word-count sanity checks
- Total runtime per company
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gpt_researcher.interview_brief import run_interview_research, InterviewBrief

TEST_COMPANIES = ["Amazon", "Google", "Microsoft", "Meta", "Netflix"]


def field_populated(brief: InterviewBrief) -> bool:
    return all([
        brief.interview_rounds,
        brief.common_topics,
        brief.tech_stack,
        brief.talking_points,
        brief.sources,
    ])


def word_count(items: list) -> int:
    return sum(len(item.split()) for item in items)


async def evaluate_company(company: str) -> dict:
    print(f"\n{'='*60}")
    print(f"Evaluating: {company}")
    print(f"{'='*60}")

    start = time.time()
    try:
        brief = await run_interview_research(company=company, verbose=False)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return {
            "company": company,
            "success": False,
            "error": str(e),
            "runtime_sec": time.time() - start,
        }

    elapsed = time.time() - start
    all_fields = field_populated(brief)
    tp_words = word_count(brief.talking_points)
    ct_words = word_count(brief.common_topics)

    result = {
        "company": company,
        "success": True,
        "all_fields_populated": all_fields,
        "interview_rounds_count": len(brief.interview_rounds),
        "common_topics_count": len(brief.common_topics),
        "tech_stack_count": len(brief.tech_stack),
        "talking_points_count": len(brief.talking_points),
        "sources_count": len(brief.sources),
        "talking_points_word_count": tp_words,
        "common_topics_word_count": ct_words,
        "runtime_sec": round(elapsed, 1),
    }

    status = "✅ PASS" if all_fields else "⚠️  PARTIAL"
    print(f"{status} | All fields populated: {all_fields}")
    print(f"   Rounds: {result['interview_rounds_count']} | "
          f"Topics: {result['common_topics_count']} | "
          f"Tech: {result['tech_stack_count']} | "
          f"Talking pts: {result['talking_points_count']} | "
          f"Sources: {result['sources_count']}")
    print(f"   Talking-points word count: {tp_words} | "
          f"Common-topics word count: {ct_words}")
    print(f"   Runtime: {elapsed:.1f}s")

    return result


async def main():
    print("Interview-Intel Agent — Evaluation Run")
    print(f"Companies: {', '.join(TEST_COMPANIES)}")

    results = []
    for company in TEST_COMPANIES:
        result = await evaluate_company(company)
        results.append(result)

    total_time = sum(r["runtime_sec"] for r in results)
    successes = sum(1 for r in results if r.get("success"))
    full_pop = sum(1 for r in results if r.get("all_fields_populated"))

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Companies tested : {len(TEST_COMPANIES)}")
    print(f"Successful runs  : {successes}/{len(TEST_COMPANIES)}")
    print(f"All fields filled: {full_pop}/{len(TEST_COMPANIES)}")
    print(f"Total runtime    : {total_time:.1f}s")
    print(f"Avg runtime      : {total_time/len(TEST_COMPANIES):.1f}s")
    print(f"\n📊 Interview-ready stat:")
    print(f'   "Successfully populated all schema fields for {full_pop}/{len(TEST_COMPANIES)} '
          f'test companies, average runtime {total_time/len(TEST_COMPANIES):.1f} seconds."')


if __name__ == "__main__":
    asyncio.run(main())