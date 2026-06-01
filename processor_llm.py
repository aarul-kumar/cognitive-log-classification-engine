from dotenv import load_dotenv
from groq import Groq
import os

load_dotenv()

def classify_with_llm(log_message):
    """Classify logs using Groq LLM"""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("[LLM] ✗ GROQ_API_KEY not set in environment")
            return None
        
        print(f"[LLM] Classifying: {log_message[:60]}...")
        groq = Groq(api_key=api_key)
        
        prompt = f'''Classify the following log message into one of these categories: 'Info', 'Warning', 'Error', 'Debug', 'Security Alert', 'System Notification', 'HTTP Status', 'User Action'.
If the message doesn't fit any category clearly, respond with 'Unclassified'.
Respond with ONLY the category name, nothing else.

Log message: {log_message}'''

        print("[LLM] Calling Groq API...")
        chat_completion = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=50
        )
        
        result = chat_completion.choices[0].message.content.strip()
        print(f"[LLM] ✓ Response: {result}")
        return result
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Invalid API Key" in error_msg:
            print(f"[LLM] ✗ Groq API Key Error: Your API key is invalid or expired")
            print(f"[LLM]    Please update your .env file with a valid GROQ_API_KEY")
            print(f"[LLM]    Get a free key from: https://console.groq.com")
        else:
            print(f"[LLM] ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print(classify_with_llm("User login failed due to invalid credentials."))
    print(classify_with_llm("System started successfully."))
    print(classify_with_llm("Disk space running low on server."))


if __name__ == "__main__":
    print(classify_with_llm("User login failed due to invalid credentials."))
    print(classify_with_llm("System started successfully."))
    print(classify_with_llm("Disk space running low on server."))