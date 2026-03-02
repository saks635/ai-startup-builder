import os

from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY_AGENT1 = os.getenv("GROQ_API_KEY_AGENT1")
if not GROQ_API_KEY_AGENT1:
    raise ValueError("GROQ_API_KEY_AGENT1 not found in .env")

idea_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY_AGENT1,
    temperature=0.3,
    max_tokens=600,
)

idea_analyzer_agent = Agent(
    role="Startup Idea Analyst",
    goal="Analyze startup ideas and return clear, structured business insights.",
    backstory=(
        "You are an experienced startup advisor focused on product clarity, "
        "market fit, and business viability."
    ),
    llm=idea_llm,
    verbose=False,
    allow_delegation=False,
    max_iter=1,
)
