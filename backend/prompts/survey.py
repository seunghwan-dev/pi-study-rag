"""
Survey agent prompts — keyword generation and paper connection analysis.
"""

SURVEY_KEYWORD_PROMPT = """You are a research survey agent for Process Informatics.

User's knowledge base:
{categories_summary}

Recent learning trend: {trend}

Generate exactly 4 arxiv search queries with different strategies:
1. REINFORCE: strengthen the weakest category ({weakest})
2. DEEPEN: follow the current interest trend ({trend})
3. BRIDGE: connect two categories for cross-domain discovery
4. DISCOVER: find emerging PI/MI trends NOT in user's current knowledge categories

Output JSON only, no markdown:
{{"keywords": ["query1", "query2", "query3", "query4"],
  "strategies": ["reinforce", "deepen", "bridge", "discover"]}}"""

SURVEY_CONNECTION_PROMPT = """Analyze how this paper connects to the user's existing knowledge.

Paper: {paper_title}
Abstract: {paper_abstract}

User's knowledge categories and coverage:
{categories_summary}

Evaluate in Japanese:
1. Which existing category does this connect to?
2. How does it extend or complement existing knowledge?
3. Relevance score (0.0 to 1.0)

Output JSON only, no markdown:
{{"connection": "説明文...", "target_category": "category_name", "relevance": 0.85}}"""

SURVEY_TREND_PROMPT = """Analyze the user's recent study questions and identify the learning trend.

Recent questions:
{questions_list}

Respond with a single short phrase (in Japanese) describing the trend topic.
Example: "転移学習の基礎理論"
No JSON, no explanation, just the trend phrase."""
