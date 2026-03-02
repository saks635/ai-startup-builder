import os
from typing import Any

from crewai import Agent, LLM
from crewai.tools import tool
from dotenv import load_dotenv

from tools.search_tool import search_market

load_dotenv()

GROQ_API_KEY_AGENT2 = os.getenv("GROQ_API_KEY_AGENT2")
if not GROQ_API_KEY_AGENT2:
    raise ValueError("GROQ_API_KEY_AGENT2 not found in .env")


@tool("market_web_search")
def market_web_search(query: str | dict[str, Any]) -> str:
    """Search the web for market, competitor, and trend signals for a startup idea."""
    if isinstance(query, dict):
        query = str(
            query.get("query")
            or query.get("description")
            or query.get("startup_idea")
            or ""
        )

    cleaned_query = query.strip()
    if not cleaned_query:
        return "No valid query was provided to market_web_search."

    return search_market(cleaned_query)


market_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY_AGENT2,
    temperature=0.2,
    max_tokens=420,
)

market_research_agent = Agent(
    role="Market Research Analyst",
    goal="Research startup markets using one web search and summarize clearly.",
    backstory="You validate startup ideas with structured market evidence.",
    llm=market_llm,
    tools=[market_web_search],
    verbose=False,
    allow_delegation=False,
    max_iter=1,
    memory=False,
)
