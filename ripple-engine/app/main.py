from fastapi import FastAPI
from pydantic import BaseModel

# Import our generator function
from . import generator

# Initialize the FastAPI app
app = FastAPI(
    title="Ripple API",
    description="An API to generate social media posts from a given text.",
    version="0.1.0"
)

# Define the data model for our request body using Pydantic.
# This ensures the incoming data is in the correct format.
class Article(BaseModel):
    text: str
    
# Define a "health check" endpoint for the root URL
from fastapi.responses import HTMLResponse
import os

# Define an endpoint to serve our main HTML file
@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Construct the path to the HTML file relative to the app directory
    html_file_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'index.html')
    with open(html_file_path) as f:
        return HTMLResponse(content=f.read(), status_code=200)

# Define the main endpoint for generating posts
@app.post("/generate")
def generate_posts_endpoint(article: Article):
    """
    Receives an article text and returns generated social media posts.
    """
    # Call our generator function with the text from the request
    posts = generator.create_ripples(article.text)
    
    if posts:
        return {"status": "success", "posts": posts}
    else:
        # If the generator fails, return an error message.
        return {"status": "error", "message": "Failed to generate posts."}