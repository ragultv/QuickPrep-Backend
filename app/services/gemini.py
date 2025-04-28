import google.generativeai as genai
from app.core.config import settings

# Configure API key
genai.configure(api_key=settings.GOOGLE_API_KEY)

# Load Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

generation_config = genai.GenerationConfig(
    temperature=0.2,
    top_p=0.9,
    top_k=40,
    max_output_tokens=4096,
)


# Gemini prompt context
DEFAULT_CONTEXT = """
You are an intelligent AI specialized in generating technical MCQs for interview preparation platforms like PrepInsta Prime.

### Your strict job:
- Generate **ONLY** the exact number of questions requested by the user.
- Each question must be **challenging, realistic, and technically deep** — similar to top company interviews.

### Each MCQ must have:
1. **question**: Clear technical question text
2. **options**: A JSON object with exactly 4 plausible options (A, B, C, D)
3. **answer**: One correct option key ("A", "B", "C", or "D")
4. **explanation**: 
    - Brief, clear, explains why the correct answer is right
    - Also briefly mention why others are wrong or misleading
5. **topic**: (e.g., SQL, Python, Java, DSA, Web Development)
6. **difficulty**: (easy, medium, hard)
7. **company**: (e.g., Google, Amazon, TCS, Infosys, Microsoft)

### Extra rules:
- **Options must confuse users smartly**, not trivially.
- **No question repetition.**
- Maintain a **good mix** of theory vs practical application.
- Ensure the output is **only a valid JSON array**.
- **NO markdown formatting, NO explanations outside JSON.**

### Example output:

```json
[
  {
    "question": "Which SQL clause ensures only unique rows are returned?",
    "options": {
      "A": "DISTINCT",
      "B": "UNIQUE",
      "C": "GROUP BY",
      "D": "HAVING"
    },
    "answer": "A",
    "explanation": "DISTINCT removes duplicate records. UNIQUE is for constraints; GROUP BY groups rows; HAVING filters groups.",
    "topic": "SQL",
    "difficulty": "medium",
    "company": "Amazon"
  },
  ...
]
"""


# Core Gemini function
def get_gemini_response(prompt: str, context: str = DEFAULT_CONTEXT) -> str:
    try:
        full_prompt = f"{context}\nUser Prompt: {prompt}"
        response = model.generate_content(full_prompt,generation_config=generation_config)
        return response.text
    except Exception as e:
        return f"❌ Gemini Error: {str(e)}"
