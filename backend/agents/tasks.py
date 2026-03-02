from crewai import Task

# ================================
# Import Agents
# ================================
from agents.idea_analyzer import idea_analyzer_agent
from agents.market_researcher import market_research_agent
from agents.website_generator import website_generator_agent
from agents.pitch_deck_generator import pitch_deck_agent


# ================================
# Idea Analysis Task (Improved)
# ================================
idea_analysis_task = Task(
    name="Idea Analysis",
    agent=idea_analyzer_agent,
    description=(
        "Analyze this startup idea: {startup_idea}.\n\n"
        "Return a comprehensive, structured analysis with these sections:\n\n"
        "## Executive Summary\n"
        "One paragraph overview of the startup opportunity.\n\n"
        "## Problem Statement\n"
        "What specific pain point does this solve? Who suffers most?\n\n"
        "## Proposed Solution\n"
        "How does the product solve this problem? Key features.\n\n"
        "## Target Audience\n"
        "Primary user personas with demographics and behavior.\n\n"
        "## Unique Value Proposition\n"
        "What makes this different from alternatives? Why now?\n\n"
        "## Revenue Model\n"
        "How will this business make money? Pricing strategy.\n\n"
        "## Competitive Moat\n"
        "What defensible advantages can be built over time?\n\n"
        "## Key Risks & Assumptions\n"
        "Top 3-5 risks and critical assumptions to validate.\n\n"
        "## Recommended Next Steps\n"
        "Immediate actions to validate this idea.\n\n"
        "Use markdown ## headings for each section. "
        "Keep bullets concise (max 3-4 per section). "
        "Be specific and actionable, avoid generic advice."
    ),
    expected_output=(
        "A comprehensive, structured startup analysis with all requested "
        "sections in markdown format using ## headings."
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


# ================================
# Pitch Deck Task
# ================================
pitch_deck_task = Task(
    name="Pitch Deck Generation",
    agent=pitch_deck_agent,
    context=[idea_analysis_task, market_research_task],
    description=(
        "Create a 10-slide investor pitch deck for this startup: {startup_idea}.\n\n"
        "Use the startup analysis and market research as context to create "
        "a compelling, data-driven pitch deck.\n\n"
        "Slides to include:\n"
        "1. Title (name + tagline)\n"
        "2. Problem\n"
        "3. Solution\n"
        "4. Market Opportunity\n"
        "5. Business Model\n"
        "6. Competitive Advantage\n"
        "7. Go-to-Market Strategy\n"
        "8. Financial Projections\n"
        "9. Team (ideal roles needed)\n"
        "10. The Ask (funding needed + use of funds)\n\n"
        "Use ## headings to separate each slide. "
        "Keep each slide to 3-5 bullet points. "
        "Be specific with numbers and data from the research. "
        "No explanations outside the slides."
    ),
    expected_output=(
        "A structured pitch deck with 10 slides using ## markdown headings."
    ),
)
