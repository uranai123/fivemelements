# check_models.py
from google import genai
import os

API_KEY = os.getenv("GOOGLE_API_KEY") 
client = genai.Client(api_key=API_KEY)

for model in client.models.list():
    print(f"モデル名: {model.name}")