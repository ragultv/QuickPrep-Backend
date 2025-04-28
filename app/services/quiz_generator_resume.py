# quiz_generator.py
import json
import re
import uuid
from typing import List, Dict
from app.services.gemini_resume import get_gemini_response


def clean_markdown_json(raw_response: str) -> str:
    """
    Final robust cleaning with enhanced comment removal
    """
    # Remove code blocks first
    cleaned = re.sub(r"```(?:json)?\n?", "", raw_response)
    
    # Remove ALL JavaScript-style comments (including multi-line)
    cleaned = re.sub(r"//.*?(\n|$)", "\n", cleaned, flags=re.DOTALL)
    
    # Remove trailing commas before brackets/braces
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    
    # Remove any remaining backticks
    cleaned = cleaned.replace("```", "")
    
    # Final cleanup of empty lines
    cleaned = "\n".join([line.strip() for line in cleaned.split("\n") if line.strip()])
    
    return cleaned.strip()


def generate_quiz(prompt: str) -> List[Dict]:
    raw_response = get_gemini_response(prompt)

    if not raw_response.strip():
        raise ValueError("Gemini returned an empty response.")

    try:
        cleaned = clean_markdown_json(raw_response)
        questions = json.loads(cleaned)
    except json.JSONDecodeError as e:
        error_position = f"Line {e.lineno}, Column {e.colno}" if hasattr(e, 'lineno') else ""
        raise ValueError(
            f"Failed to parse Gemini response: {e}\n"
            f"Error Position: {error_position}\n"
            f"Cleaned Output:\n{cleaned}\n"
            f"Raw Output:\n{raw_response}"
        )

    validated_questions = []
    for idx, item in enumerate(questions):
        try:
            # Validate required fields
            if not all(key in item for key in ["question", "options", "answer"]):
                print(f"Skipping question {idx} - missing required fields")
                continue

            options = item["options"]
            if not all(k in options for k in ["A", "B", "C", "D"]):
                print(f"Skipping question {idx} - missing required options")
                continue

            validated_questions.append({
                "question_text": item["question"],
                "option_a": options["A"],
                "option_b": options["B"],
                "option_c": options["C"],
                "option_d": options["D"],
                "topic": item.get("topic", "General"),
                "difficulty": item.get("difficulty", "medium"),
                "correct_answer": item["answer"].upper(),
                "explanation": item.get("explanation", "Explanation not provided"),
                "company": item.get("company")
            })
        except (KeyError, TypeError, AttributeError) as e:
            print(f"Skipping invalid question {idx}: {str(e)}")
            continue

    if not validated_questions:
        raise ValueError("No valid questions found in Gemini response")

    return validated_questions