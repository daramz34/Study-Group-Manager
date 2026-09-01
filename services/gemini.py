from google import genai
import json
from datetime import datetime
from core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL = "gemini-2.5-flash"


def parse_json_response(response_text: str):
    """" Clean and parse the JSON response from the Gemini API. """

    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)



# generate quiz questions

async def generate_quiz_questions(topic_content: str) -> list[dict]:
    """Generate 5 quiz questions based on study topic"""

    prompt = f""" You are a quiz generator for students. Based on this study material,
    generate 5 questions to test comprehension.
    
    Mix question types:
    - 2 multiple choice (4 options each)
    - 1 true/false
    - 2 short answer
    
    Study Material: {topic_content}
    Return ONLY valid JSON:
    {{
        "questions": [
            {{
                "id": 1,
                "type": "multiple_choice",
                "question": "What is...?",
                "options": ["A. Option1", "B. Option2", "C. Option3", "D. Option4"],
                "correct_answer": "B"
            }},
            {{
                "id": 2,
                "type": "true_false",
                "question": "...",
                "correct_answer": "True"
            }},
            {{
                "id": 3,
                "type": "short_answer",
                "question": "...",
                "correct_answer": "..."
            }}
        ]
    }}
    """

    response = await client.aio.models.generate_content(model=MODEL, contents=prompt)

    response_text = parse_json_response(response.text)

    return response_text.get("questions", [])



# quiz answers

async def grade_quiz_answers(topic_content: str, questions: list[dict], answers: list[str]) -> dict:
    """Grade user answers against the topic"""

    prompt = f"""
    You are a strict but fair grader. Grade each answer.
    
    Scoring:
    - 2 = Correct (matches answer or demonstrates understanding)
    - 1 = Partial (close but missing key detail)
    - 0 = Wrong or blank

    Study Topic: {topic_content}
    
    Questions with Correct Answers:
    {json.dumps(questions, indent=2)}
    
    Student's Answers (in same order as questions):
    {json.dumps(answers, indent=2)}
    
    Return ONLY valid JSON:
    {{
        "results": [
            {{
                "question_id": 1,
                "score": 2,
                "feedback": "Correct! Your answer shows..."
            }},
            {{
                "question_id": 2,
                "score": 0,
                "feedback": "Incorrect. The right answer is..."
            }}
        ],
        "total_score": 8,
        "max_score": 10,
        "summary": "Strong understanding of X, review Y concepts."
    }}
    """

    response = await client.aio.models.generate_content(model=MODEL, contents=prompt)
    response_text = parse_json_response(response.text)

    return response_text

async def generate_weekly_digest(group_name: str, member_stats: list[dict]) -> str:
    """Generate plain text summary of weekly activity"""

    prompt = f""" 
    Write a brief, encouraging weekly summary for a study group.
    
    Group: {group_name}
    Week: {datetime.now().strftime("%B %d, %Y")}
    
    Member Activity:
    {json.dumps(member_stats, indent=2)}
    
    Include:
    - Total quizzes completed this week
    - Top performer(s) with points
    - Group average score
    - Streak updates
    - Motivational closing
    
    Keep it under 150 words. Plain text only, no JSON."""

    response = await client.aio.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()
