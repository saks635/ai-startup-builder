import os

from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

pitch_deck_llm = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=GEMINI_API_KEY,
    temperature=0.3,
    max_tokens=1800,
)

pitch_deck_agent = Agent(
    role="Pitch Deck Creator",
    goal=(
        "Create a compelling, investor-ready pitch deck from startup analysis "
        "and market research data."
    ),
    backstory=(
        "You are a seasoned startup advisor and pitch coach who has helped "
        "hundreds of startups craft winning pitch decks that secured funding."
    ),
    llm=pitch_deck_llm,
    verbose=False,
    allow_delegation=False,
    max_iter=2,
    tools=[],
    system_message=(
        "Create a pitch deck with exactly these slides using markdown ## headings:\n\n"
        "## Title\n"
        "Startup name and a one-line tagline.\n\n"
        "## Problem\n"
        "What pain point exists? Use 2-3 bullet points.\n\n"
        "## Solution\n"
        "How does this startup solve it? 2-3 bullet points.\n\n"
        "## Market Opportunity\n"
        "TAM/SAM/SOM or market size signals. Use data from market research.\n\n"
        "## Business Model\n"
        "How it makes money. Revenue streams and pricing approach.\n\n"
        "## Competitive Advantage\n"
        "What makes this different? Moat and differentiators.\n\n"
        "## Go-to-Market Strategy\n"
        "How to acquire first 1000 users. Channels and tactics.\n\n"
        "## Financial Projections\n"
        "Rough 3-year projection. Key metrics and milestones.\n\n"
        "## Team\n"
        "Ideal founding team roles needed.\n\n"
        "## The Ask\n"
        "What funding/resources are needed and what they'll be used for.\n\n"
        "Rules:\n"
        "- Use ## headings to separate slides\n"
        "- Keep each slide concise (3-5 bullet points max)\n"
        "- Use real data from the analysis and market research context\n"
        "- Be specific with numbers where possible\n"
        "- No explanations outside the slides\n"
    ),
)
