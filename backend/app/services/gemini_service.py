import os

from google import genai
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


# Get Gemini API key from environment
api_key = os.getenv("GEMINI_API_KEY")


def ask_gemini(prompt: str) -> str:

    # Stop if API key has not been configured
    if not api_key:
        return "Gemini API key is not configured."

    # Create Gemini client
    client = genai.Client(api_key=api_key)

    # Send prompt using the newer Interactions API
    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt,
    )

    # Return Gemini's text response
    return interaction.output_text