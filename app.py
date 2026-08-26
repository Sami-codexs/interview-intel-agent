"""Streamlit frontend for the Interview-Intel Agent."""

import asyncio
import os
from datetime import datetime, timezone

import streamlit as st

from gpt_researcher.interview_brief import run_interview_research

st.set_page_config(
    page_title="Interview-Intel Agent",
    page_icon="🎯",
    layout="centered",
)

st.title("🎯 Interview-Intel Agent")
st.caption("Autonomous research agent that generates structured interview prep briefs")

required = ["GROQ_API_KEY", "TAVILY_API_KEY", "FAST_LLM", "SMART_LLM", "EMBEDDING"]
missing = [v for v in required if not os.getenv(v)]

if missing:
    st.error(f"Missing environment variables: {', '.join(missing)}")
    with st.expander("🔧 How to set secrets in Streamlit Cloud"):
        st.code("""
[general]
GROQ_API_KEY = "gsk_..."
TAVILY_API_KEY = "tvly-..."
FAST_LLM = "groq:openai/gpt-oss-20b"
SMART_LLM = "groq:openai/gpt-oss-120b"
EMBEDDING = "huggingface:sentence-transformers/all-MiniLM-L6-v2"
GITHUB_TOKEN = "ghp_...  # optional"
""", language="toml")
    st.stop()

company = st.text_input(
    "Company name",
    placeholder="e.g. Amazon, Google, Netflix, Stripe",
)

generate = st.button("🔍 Generate Brief", use_container_width=True)

if generate and company:
    with st.spinner(f"Researching **{company}**… This takes ~45–60 seconds"):
        try:
            brief = asyncio.run(run_interview_research(company.strip(), verbose=False))

            st.success(f"✅ Brief generated for **{brief.company}**")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Rounds", len(brief.interview_rounds))
            c2.metric("Topics", len(brief.common_topics))
            c3.metric("Tech Stack", len(brief.tech_stack))
            c4.metric("Sources", len(brief.sources))

            t1, t2, t3, t4 = st.tabs([
                "📋 Rounds & Topics",
                "💻 Tech Stack",
                "🗣️ Talking Points",
                "🔗 Sources",
            ])

            with t1:
                st.subheader("Interview Rounds")
                for r in brief.interview_rounds:
                    st.markdown(f"- {r}")
                st.subheader("Common Topics")
                for topic in brief.common_topics:
                    st.markdown(f"- {topic}")

            with t2:
                if brief.tech_stack:
                    st.code("\n".join(brief.tech_stack))
                else:
                    st.info("No tech stack data found.")

            with t3:
                for tp in brief.talking_points:
                    st.info(tp)

            with t4:
                for url in brief.sources:
                    st.markdown(f"- [{url}]({url})")

            md = f"""# Interview Prep Brief: {brief.company}
Generated: {datetime.now(timezone.utc).isoformat()}Z

## Interview Rounds
{chr(10).join("- " + r for r in brief.interview_rounds)}

## Common Topics
{chr(10).join("- " + t for t in brief.common_topics)}

## Tech Stack
{chr(10).join("- " + t for t in brief.tech_stack)}

## Talking Points
{chr(10).join("- " + tp for tp in brief.talking_points)}

## Sources
{chr(10).join("- " + s for s in brief.sources)}
"""

            st.download_button(
                "📥 Download Markdown",
                data=md,
                file_name=f"{brief.company.lower().replace(' ', '_')}_brief.md",
                mime="text/markdown",
            )

        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.exception(e)