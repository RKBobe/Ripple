import google.generativeai as genai
import os
import json
import sys

# Configure the API on module load.
# This is safe because Python only runs this once when the module is first imported.
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # In a server context, we log the error rather than exit the whole process.
        print("FATAL ERROR: GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key, transport='rest')
except Exception as e:
    print(f"Error configuring GenerativeAI: {e}")


def get_prompt(text: str) -> str:
    """Creates the detailed prompt for the LLM."""
    return f"""
Analyze the following article and generate a set of social media posts based on its content.
The output must be a valid JSON object.

The JSON object must have a key called "social_posts" which is an array of post objects.
Each post object in the array must have these keys:
- "platform": The name of the social media platform (e.g., "Twitter", "LinkedIn").
- "content": The text of the post, written in a style appropriate for the platform.
- "hashtags": An array of relevant hashtags as strings, without the '#' symbol.

Generate the following posts:
1. Two "Twitter" posts. They must be engaging and under 280 characters. Use emojis.
2. One "LinkedIn" post. It should be professional and insightful.
3. One "Key Takeaways" post for a general audience using bullet points. Use "General" as the platform.

Article to analyze:
---
{text}
---
"""

def create_ripples(article_text: str) -> list | None:
    """
    The main function to generate social media posts.
    Takes article text and returns a list of post dictionaries or None on failure.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = get_prompt(article_text)
        response = model.generate_content(prompt)
        
        cleaned_json = response.text.strip().lstrip("```json").rstrip("```")
        data = json.loads(cleaned_json)
        return data.get('social_posts')

    except Exception as e:
        print(f"An error occurred in create_ripples: {e}")
        return None