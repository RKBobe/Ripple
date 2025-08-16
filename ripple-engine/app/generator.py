import google.generativeai as genai
import os
import json
import sys
from typing import List

# Configure the API on module load.
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("FATAL ERROR: GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key, transport='rest')
except Exception as e:
    print(f"Error configuring GenerativeAI: {e}")


def get_prompt(text: str, platforms: List[str]) -> str:
    """Creates a detailed, dynamic prompt for the LLM based on selected platforms."""
    
    # Define the specific instructions for each platform
    platform_instructions = {
        "Twitter": "One 'Twitter' post. It must be engaging, under 280 characters, and use emojis.",
        "LinkedIn": "One 'LinkedIn' post. It should be professional, insightful, and aimed at a business audience.",
        "Facebook": "One 'Facebook' post. It should be friendly and conversational, encouraging comments and shares.",
        "Pinterest": "One 'Pinterest' Pin description. It should be keyword-rich, descriptive, and inspiring, suitable for an image or infographic related to the text.",
        "Reddit": "One 'Reddit' post title and body. The title should be engaging or controversial to spark discussion. The body should provide a brief summary and a question for the community."
    }

    # Build the list of requested posts based on the user's selection
    requested_posts = [platform_instructions[p] for p in platforms if p in platform_instructions]
    
    # If no valid platforms are selected, create a default generic post
    if not requested_posts:
        requested_posts.append("One 'General' post, summarizing the key takeaways in bullet points.")

    post_list_str = "\n".join(f"- {i+1}. {req}" for i, req in enumerate(requested_posts))

    return f"""
Analyze the following article and generate a set of social media posts based on its content.
The output must be a valid JSON object.

The JSON object must have a key called "social_posts" which is an array of post objects.
Each post object in the array must have these keys:
- "platform": The name of the social media platform.
- "content": The text of the post, written in a style appropriate for the platform.
- "hashtags": An array of relevant hashtags as strings, without the '#' symbol.

Generate the following posts:
{post_list_str}

Article to analyze:
---
{text}
---
"""

def create_ripples(article_text: str, platforms: List[str]) -> list | None:
    """
    The main function to generate social media posts.
    Takes article text and a list of platforms, then returns a list of post dictionaries.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = get_prompt(article_text, platforms) # Pass platforms to the prompt function
        response = model.generate_content(prompt)
        
        cleaned_json = response.text.strip().lstrip("```json").rstrip("```")
        data = json.loads(cleaned_json)
        return data.get('social_posts')

    except Exception as e:
        print(f"An error occurred in create_ripples: {e}")
        return None