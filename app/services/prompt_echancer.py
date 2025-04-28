import google.generativeai as genai
from backend.app.core.config import settings

# Configure API key
genai.configure(api_key=settings.GOOGLE_API_KEY)

# Load Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

DEFAULT_CONTEXT = """
You are a prompt refinement assistant. Your task is to analyze and enhance user prompts for quiz question generation by:

1. Making them more specific and unambiguous
2. Clarifying the scope and difficulty level
3. Suggesting clearer wording while preserving the original intent
4. Eliminating vagueness or ambiguity
5. If no difficulty is mentioned, default to medium difficulty
6. If no topic is mentioned, default to basic to intermediate topics
7. Keep the refined prompt short, similar to the original
8. Do NOT ask the user for more details — only improve the given prompt
9. Do NOT add requirements like multiple-choice format, answer keys, or scoring unless explicitly mentioned
10. Always use numerical values for quantities (e.g., "10 questions" not "ten questions")

Focus solely on enhancing the prompt for optimal quiz generation.
"""

def get_gemini_response(prompt: str, context: str = DEFAULT_CONTEXT) -> str:
    try:
        full_prompt = f"{context}\nUser Prompt: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"❌ Gemini Error: {str(e)}"
