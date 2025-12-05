from dotenv import load_dotenv
from groq import Groq
load_dotenv()
groq = Groq()


def classify_with_llm(log_message):
    prompt = f'''Classify the following log message into one of the categories: 'Info', 'Warning', 'Error', 'Debug'. If the message does not fit any category, respond with 'Unclassified'. Only respond with the category name. No preamble. Log message: {log_message}'''

    chat_completion = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt,}
        ])
    return chat_completion.choices[0].message.content

if __name__ == "__main__":
    print(classify_with_llm("User login failed due to invalid credentials."))
    print(classify_with_llm("System started successfully."))
    print(classify_with_llm("Disk space running low on server."))