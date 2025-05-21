from openai import OpenAI

# Replace this with your actual OpenRouter API key
OPENROUTER_API_KEY = "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"
NVIDIA_API_KEY="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"

Nvidia_client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = NVIDIA_API_KEY
)

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

MODEL_NAME_NVIDIA = "nvidia/llama-3.1-nemotron-ultra-253b-v1"
MODEL_NAME_OPENROUTER = "openai/gpt-4o-mini"


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

def get_openrouter_response(prompt: str, context: str = DEFAULT_CONTEXT) -> str:
    try:
        full_prompt = f"{context.strip()}\nUser Prompt: {prompt.strip()}"

        completion = openrouter_client.chat.completions.create(
            model=MODEL_NAME_OPENROUTER,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.2,
            top_p=0.9,
            max_tokens=4096
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ OpenRouter Error: {str(e)}"

def get_nvidia_response(prompt: str, context: str = DEFAULT_CONTEXT) -> str:
    try:
        full_prompt = f"{context.strip()}\nUser Prompt: {prompt.strip()}"

        completion = Nvidia_client.chat.completions.create(
            model=MODEL_NAME_NVIDIA,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.6,
            top_p=0.95,
            max_tokens=4096,
            frequency_penalty=0,
            presence_penalty=0,
            stream=True
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Nvidia Error: {str(e)}"
