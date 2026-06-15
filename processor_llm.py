from dotenv import load_dotenv
from groq import Groq
import os
import json

load_dotenv()

def classify_with_llm(log_message):
    """Classify logs using Groq LLM and return reasoning tokens in strict JSON format"""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("[LLM] ✗ GROQ_API_KEY not set in environment")
            return None
            
        groq = Groq(api_key=api_key)
        
        prompt = f'''Analyze this log message: "{log_message}"
Classify it into one of these categories: 'Info', 'Warning', 'Error', 'Debug', 'Security Alert', 'System Notification', 'HTTP Status', 'User Action'. If it does not fit, use 'Unclassified'.

Respond ONLY with a raw, valid JSON object exactly matching this format:
{{"category": "CategoryName", "reasoning_tokens": ["token1", "token2"]}}

Rules for reasoning_tokens:
- Extract exactly 1 to 3 specific, verbatim words or short phrases directly from the log message that justify the classification.
- Do not write sentences, just the exact sub-strings.'''

        chat_completion = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=100,
            response_format={"type": "json_object"}
        )
        
        result_text = chat_completion.choices[0].message.content.strip()
        parsed = json.loads(result_text)
        
        return {
            "category": parsed.get("category", "Unclassified"),
            "reasoning_tokens": parsed.get("reasoning_tokens", [])
        }
        
    except json.JSONDecodeError as e:
        print(f"[LLM] ✗ JSON Parsing Error: {e}")
        return None
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Invalid API Key" in error_msg:
            print(f"[LLM] ✗ Groq API Key Error: Your API key is invalid or expired")
        else:
            print(f"[LLM] ✗ Error: {e}")
        return None

if __name__ == "__main__":
    print(classify_with_llm("User login failed due to invalid credentials."))