import json
import re
from typing import List, Dict
from app.services.gemini_resume import get_gemini_response,get_bulk_gemini_response


def clean_markdown_json(raw_response: str) -> str:
    # Remove markdown code blocks and HTML comments
    cleaned = re.sub(r"```(?:json)?\n?", "", raw_response)
    cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)
    
    # Fix trailing commas in arrays/objects
    cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
    
    # Remove invalid control characters
    cleaned = re.sub(r"[\x00-\x1F\x7F]", "", cleaned)
    
    # Extract first valid JSON array with bracket counting
    stack = []
    start_idx = None
    for idx, ch in enumerate(cleaned):
        if ch == '[':
            if not stack:
                start_idx = idx
            stack.append(ch)
        elif ch == ']':
            if stack and stack[-1] == '[':
                stack.pop()
                if not stack:  # Found complete array
                    json_str = cleaned[start_idx:idx+1]
                    # Validate with actual JSON parser
                    try:
                        json.loads(json_str)
                        return json_str
                    except json.JSONDecodeError:
                        continue
    raise ValueError("❌ Could not extract valid JSON array")


def generate_single_batch(prompt: str, total_questions: int) -> List[Dict]:
    """
    Generate and validate a batch of questions from Gemini response.
    Returns list of properly formatted question dictionaries.
    """
    try:
        # Choose the appropriate Gemini call based on total_questions
        if total_questions <= 50:
            raw_response = get_gemini_response(prompt)
        else:
            raw_response = get_bulk_gemini_response(prompt)

        if not raw_response.strip():
            raise ValueError("Empty response from Gemini")

        # Clean and parse JSON (for both cases)
        cleaned_json = clean_markdown_json(raw_response)
        try:
            questions_data = json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            print("Raw AI response:", cleaned_json)  # Log the cleaned response for debugging
            raise ValueError(f"Invalid JSON format: {str(e)}")

        # Validate root structure
        if not isinstance(questions_data, list):
            raise ValueError("Top-level structure must be a JSON array")

        validated_questions = []

        # Process each question item
        for idx, item in enumerate(questions_data):
            if not all(key in item for key in ("question", "options", "answer")):
                continue

            options = item.get("options", {})
            if not all(k in options for k in ("A", "B", "C", "D")):
                continue

            try:
                transformed = {
                    "question_text": item["question"],
                    "option_a": options["A"],
                    "option_b": options["B"],
                    "option_c": options["C"],
                    "option_d": options["D"],
                    "correct_answer": str(item["answer"]).upper().strip(),
                    "explanation": item.get("explanation", ""),
                    "topic": item.get("topic", "General"),
                    "difficulty": item.get("difficulty", "medium").lower(),
                    "company": item.get("company", "Unknown")
                }

                if transformed["correct_answer"] not in ("A", "B", "C", "D"):
                    continue

                validated_questions.append(transformed)

            except KeyError:
                continue

        if not validated_questions:
            raise ValueError("No valid questions found in batch response")

        return validated_questions

    except Exception as e:
        error_msg = f"Batch generation failed: {str(e)}"
        print(f"🔥 {error_msg}")
        raise ValueError(error_msg)

    

def generate_large_quiz(
    prompt: str,
    total_questions: int = 500,
    batch_size: int = 20
) -> List[Dict]:
    full: List[Dict] = []
    # Keep track of all question texts to ensure global uniqueness
    all_question_texts = set()
    
    while len(full) < total_questions:
        remaining = total_questions - len(full)
        current_batch_size = min(batch_size, remaining)

        total_questions=total_questions
        batch_prompt = (
            f"{prompt}\n\n"
            f"CRITICAL: Generate EXACTLY {current_batch_size} UNIQUE questions. "
            f"DO NOT RETURN MORE THAN {current_batch_size} ITEMS. "
            f"Make sure each question is different from previous ones. "
            f"Current progress: {len(full)}/{total_questions} generated."
        )
        
        unique_batch = []
        try:
            batch =generate_single_batch(batch_prompt,total_questions)
            
            # Filter out any questions that duplicate previously generated ones
            for question in batch:
                if question["question_text"] not in all_question_texts:
                    unique_batch.append(question)
                    all_question_texts.add(question["question_text"])
                else:
                    print(f"Found duplicate question")
            
            # If batch is incomplete after filtering, generate missing questions
            if len(unique_batch) < current_batch_size:
                print(f"Short batch after uniqueness check: {len(unique_batch)}/{current_batch_size}")
                unique_batch = fill_missing_questions(prompt, unique_batch, current_batch_size, all_question_texts)
            
            # Add batch to full set
            full.extend(unique_batch)
            print(f"Progress: {len(full)}/{total_questions} unique questions generated")
            
        except Exception as e:
            print(f"Batch generation error: {str(e)}")
            # If we have some questions, continue with what we have
            if len(unique_batch) > 0:
                full.extend(unique_batch)
                print(f"Added partial batch of {len(unique_batch)} questions")
        
    return full[:total_questions]

def fill_missing_questions(
    prompt: str, 
    current_batch: List[Dict], 
    target_size: int,
    all_question_texts: set,
    max_attempts: int = 3
) -> List[Dict]:
    """
    Generates exactly the missing number of questions needed to complete a batch,
    ensuring global uniqueness across all batches.
    
    Args:
        prompt: The base prompt to use
        current_batch: The current incomplete batch of questions
        target_size: The desired batch size
        all_question_texts: Set of all question texts already generated
        max_attempts: Maximum number of attempts to fill the batch
    
    Returns:
        List[Dict]: The completed batch with additional questions
    """
    # Calculate exactly how many questions are missing
    total_questions = target_size - len(current_batch)
    
    if total_questions <= 0:
        return current_batch  # Batch is already complete
    
    print(f"Attempting to generate exactly {total_questions} missing unique questions...")
    
    combined_batch = current_batch.copy()
    
    attempts = 0
    while len(combined_batch) < target_size and attempts < max_attempts:
        try:
            # Create a prompt specifically for the missing questions
            fill_prompt = (
                f"{prompt}\n\n"
                f"CRITICAL: Generate EXACTLY {total_questions} unique questions. "
                f"I already have {len(current_batch)} questions in this batch. "
                f"I need EXACTLY {total_questions} MORE UNIQUE questions to complete the batch."
            )
            
            # Generate just the missing questions
            additional_questions =generate_single_batch(fill_prompt,total_questions)
            
            # Filter out any duplicates against ALL previously generated questions
            added_count = 0
            for q in additional_questions:
                if q["question_text"] not in all_question_texts:
                    combined_batch.append(q)
                    all_question_texts.add(q["question_text"])
                    added_count += 1
            
            # If we still need more, calculate how many are still missing
            still_missing = target_size - len(combined_batch)
            if still_missing > 0:
                print(f"Added {added_count} unique questions. Still need {still_missing} more.")
                missing_count = still_missing
            else:
                print(f"Successfully added {added_count} unique questions to complete the batch.")
                break
                
        except Exception as e:
            print(f"Error generating missing questions: {str(e)}")
        
        attempts += 1
    
    print(f"Final batch size: {len(combined_batch)}/{target_size}")
    return combined_batch