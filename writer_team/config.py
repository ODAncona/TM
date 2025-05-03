import os
from dotenv import load_dotenv
from langchain_cerebras import ChatCerebras

load_dotenv()

def get_llm():
    return ChatCerebras(
        model="llama-4-scout-17b-16e-instruct",
        api_key=os.getenv("CEREBRAS_API_KEY")
    )