# tests/test_openai_connection.py
import os
from dotenv import load_dotenv
from openai import OpenAI

print("--- Starting OpenAI Connection Test ---")

# Manually load the environment variables from .env file
# We go up one level ('..') to find the root directory where .env is located
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Get the API key from the loaded environment
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("!!! FAILURE: OPENAI_API_KEY not found in environment. Check your .env file.")
else:
    print("API Key found successfully.")
    try:
        # Try to create a client and make a simple API call
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'hello'."}]
        )
        print("OpenAI API call successful!")
        print("Response:", response.choices[0].message.content)
        print("\n--- TEST PASSED ---")
    except Exception as e:
        print(f"!!! FAILURE: An error occurred during the API call: {e}")