import google.generativeai as genai
from app.core.config import settings

# Configure API key


generation_config = genai.GenerationConfig(
    temperature=0.2,
    top_p=0.9,
    top_k=40,
    max_output_tokens=4096,
)


# Gemini prompt context
DEFAULT_CONTEXT = """
You are an intelligent AI specialized in generating high-quality MCQs for competitive exams, interviews, and learning platforms like PrepInsta Prime.

### Your strict job:
- Generate **ONLY** the exact number of questions requested by the user.
- Questions must be **challenging, realistic, and well-crafted** — suitable for preparation for jobs, college placements, and aptitude tests.

### Each MCQ must have:
1. **question**: Clear and concise question text
2. **options**: A JSON object with exactly 4 plausible options (A, B, C, D)
3. **answer**: One correct option key ("A", "B", "C", or "D")
4. **explanation**: 
    - Clear and helpful
    - Explains why the correct answer is right and why the others are wrong/misleading
5. **topic**: (e.g., Aptitude, Verbal, Logical Reasoning, Current Affairs, SQL, Python, Java, DSA, Web Development, etc.)
6. **difficulty**: (easy, medium, hard)
7. **company**: (e.g., Google, Amazon, TCS, Infosys, Common Exam, NA if not company-specific)

### Additional rules:
- **Options must be well-thought and create healthy confusion**, not obvious.
- **No question repetition.**
- Maintain a **good mix of theoretical and practical questions** when relevant.
- Output **only a valid JSON array.**
- **Do NOT use markdown or any text outside the JSON.**
## Example output
[
  {
    "question": "question?",
    "options": {
      "A": "option a",
      "B": "option b",
      "C": "option c",
      "D": "option d"
    },
    "answer": "A",
    "explanation": "explanation",
    "topic": "topic",
    "difficulty": "medium",
    "company": "company, if not leave"
  }
]

"""


def get_gemini_response(prompt: str, context: str = DEFAULT_CONTEXT) -> str:
    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)  # dynamically set standard key
        model = genai.GenerativeModel("gemini-1.5-flash")
        full_prompt = f"{context}\nUser Prompt: {prompt}"
        response = model.generate_content(full_prompt, generation_config=generation_config)
        return response.text
    except Exception as e:
        return f"❌ Gemini Error: {str(e)}"


# Function to get response using BULK Gemini API Key
def get_bulk_gemini_response(prompt: str, context: str = DEFAULT_CONTEXT) -> str:
    try:
        genai.configure(api_key=settings.BULK_GOOGLE_API_KEY)  # dynamically set bulk key
        model = genai.GenerativeModel("gemini-1.5-flash")
        full_prompt = f"{context}\nUser Prompt: {prompt}"
        response = model.generate_content(full_prompt, generation_config=generation_config)
        return response.text
    except Exception as e:
        return f"❌ Gemini Bulk Error: {str(e)}"