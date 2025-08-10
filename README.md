
# 💧 Ripple

Ripple is a micro-SaaS that takes a long-form piece of text (like an article or blog post) and "ripples" it out into a set of smaller posts formatted for various social media platforms.

---

### Current Status: Functional MVP

The project is currently a functional Minimum Viable Product (MVP).

**Completed Features:**

- **Backend API:** A server built with **FastAPI** that exposes an endpoint to generate content.
- **Core Engine:** A generator module that uses the **Google Gemini API** to analyze text and create social media posts.
- **Frontend UI:** A simple, single-page interface built with **HTML, CSS, and vanilla JavaScript** that allows a user to input text and see the generated results.

---

### Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **AI Engine:** Google Generative AI (Gemini)
- **Frontend:** HTML, CSS, JavaScript
- **Database (Next Step):** SQLModel with SQLite

---

### Local Setup & Running

1. **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd ripple-engine
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set Environment Variable:**
    - Create a `.env` file in the root directory and add your API key: `GOOGLE_API_KEY="YOUR_API_KEY_HERE"`
    - *Or, for Codespaces, set it as a repository secret named `GOOGLE_API_KEY`.*

5. **Run the application server:**

    ```bash
    uvicorn app.main:app --reload
    ```

6. Open your browser to `http://127.0.0.1:8000`.
