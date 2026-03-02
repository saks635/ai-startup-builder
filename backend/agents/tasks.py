from crewai import Task

# ================================
# Import Agents
# ================================
from agents.idea_analyzer import idea_analyzer_agent
from agents.market_researcher import market_research_agent
from agents.website_generator import website_generator_agent


# ================================
# Idea Analysis Task
# ================================
idea_analysis_task = Task(
    name="Idea Analysis",
    agent=idea_analyzer_agent,
    description=(
        "Analyze this startup idea: {startup_idea}.\n\n"
        "Return sections for:\n"
        "- Problem Statement\n"
        "- Proposed Solution\n"
        "- Target Users\n"
        "- Unique Value Proposition\n"
        "- Monetization Strategy\n"
        "- Risks and Assumptions\n\n"
        "Keep it concise. Use short bullets only."
    ),
    expected_output=(
        "A concise, structured analysis with all requested "
        "sections in markdown."
    ),
)


# ================================
# Market Research Task
# ================================
market_research_task = Task(
    name="Market Research",
    agent=market_research_agent,
    context=[idea_analysis_task],
    description=(
        "Research the market for this startup idea: {startup_idea}.\n\n"
        "Call the market_web_search tool once to gather signals.\n"
        "Then produce a structured markdown report including:\n"
        "- Competitors\n"
        "- Market Demand\n"
        "- Funding Signals\n"
        "- Industry Trends\n"
        "- Gaps and Opportunities\n\n"
        "Keep it concise. Max 3 bullets per section."
    ),
    expected_output="Structured markdown market research report."
)




# ================================
# Website Generation Task
# ================================
website_generation_task = Task(
    name="Website Generation",
    agent=website_generator_agent,
    context=[idea_analysis_task, market_research_task],
    description=(
        "Generate ONLY index.html for this startup: {startup_idea}.\n\n"
        "Use analysis and market research context for strong copy.\n\n"
        "Output exactly one file block:\n"
        "FILE: index.html\n"
        "```html\n"
        "<full html>\n"
        "```\n\n"
        "Rules:\n"
        "- Include nav links to index.html, about.html, pricing.html, contact.html.\n"
        "- Keep code concise but visually polished.\n"
        "- Prioritize clear section spacing and conversion-focused layout.\n"
        "- No explanations outside file block."
    ),
    expected_output=(
        "A single FILE block for index.html."
    ),
)
