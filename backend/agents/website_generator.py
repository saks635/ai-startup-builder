import os

from crewai import Agent, LLM
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

website_llm = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=GEMINI_API_KEY,
    temperature=0.25,
    max_tokens=1400,
)

website_generator_agent = Agent(
    role="Landing Page Generator",
    goal=(
        "Generate a polished, high-converting startup landing page as index.html. "
        "Other pages and shared assets are assembled by the workflow."
    ),
    backstory=(
        "You are a senior frontend engineer and copywriter focused on fast, clean, "
        "semantic HTML output with conversion-focused content."
    ),
    llm=website_llm,
    verbose=False,
    allow_delegation=False,
    max_iter=2,
    tools=[],
    system_message=(
        "Output exactly one file block in this format:\n"
        "FILE: index.html\n"
        "```html\n"
        "<full html>\n"
        "```\n\n"
        "Rules:\n"
        "- Generate only index.html.\n"
        "- Include nav links to index.html, about.html, pricing.html, contact.html.\n"
        "- Use semantic sections (hero, features, social proof, CTA, footer).\n"
        "- Use clean class names for layout: hero, hero-grid, panel, feature-grid, section, btn, btn-primary, btn-ghost.\n"
        "- Focus on clear visual hierarchy, whitespace, and well-grouped content blocks.\n"
        "- Use modern product copy and short, scannable text.\n"
        "- Do not inline large CSS or JS blocks.\n"
        "- Keep output concise and production-usable.\n"
        "- Do not add explanations outside the file block.\n"
    ),
)
