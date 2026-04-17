"""
Quiz mode prompts — question generation and answer evaluation.
"""

QUIZ_GENERATE_PROMPT = """Based on the following passage from an academic paper, generate ONE exam question.

CRITICAL RULES:
1. The question should require explanation, not just yes/no.
2. Use Japanese.
3. Make it exam-appropriate difficulty.
4. IMPORTANT: If the passage references "Table N", "Figure N", "Section N", you MUST describe the content of that reference within the question itself.
   BAD: "表11から何が読み取れるか？"
   GOOD: "表11(ハイパーパラメータチューニング時間と精度の関係を示す)から何が読み取れるか？"
5. The question must be self-contained — a student should understand what is asked without seeing the original passage.

Passage: {chunk_text}
Source: {doc_title}, {page_hint}

Output JSON only, no markdown:
{{"question": "...", "difficulty": "basic|intermediate|advanced"}}"""

QUIZ_EVALUATE_PROMPT = """Question: {question}
Reference answer (from paper): {chunk_text}
Student's answer: {user_answer}

Evaluate:
1. Score: correct / partially_correct / incorrect
2. What did they get right?
3. What did they miss or get wrong?
4. Provide the complete answer with source citation.
Use Japanese.

CITATION RULES for complete_answer:
- Use [1] numbered citations if referencing the retrieved passage (only one passage is provided, so [1] is the only valid number).

"source" field rules (STRICT):
- Output ONLY a single short Japanese phrase like "論文本文" or "論文の結論部分".
- Alternatively, output an empty string "".
- FORBIDDEN: English phrases, "Student's analysis", "based on context", section codes like "D.1" or "Appendix A".
- Example GOOD: "論文本文", "論文の結論部分", ""
- Example BAD: "D.1", "Appendix A", "Student's analysis", "based on the context above"

Output JSON only, no markdown:
{{
  "score": "correct|partially_correct|incorrect",
  "feedback": "...",
  "complete_answer": "...",
  "source": "..."
}}"""
