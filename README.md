# Recursive Research Agent

An AI-powered research tool built with **FastAPI**, **LangGraph**, **Groq (LLaMA)**, and **Neon Postgres**.  
The agent writes a research report, auto-identifies technical terms, defines them, and returns an annotated  report — all saved to your personal history.

---

## 📁 Project Structure

```
recursive-research-agent/
├── app.py                  # FastAPI entry point — all routes & middleware
├── core/
│   ├── agent.py            # LangGraph pipeline (4 nodes: research → analyze → define → compile)
│   ├── auth.py             # JWT creation, password hashing, get_current_user dependency
│   ├── database.py         # Neon Postgres connection helper (db_execute)
│   └── models.py           # Pydantic request/response schemas + AgentState TypedDict
├── templates/
│   └── index.html          # Jinja2 HTML template (served at /)
├── static/
│   ├── css/
│   │   └── style.css       # All custom styles
│   └── js/
│       └── script.js       # All frontend JavaScript
├── .env                    # Local secrets (never commit)
├── .gitignore
├── Dockerfile              # For Hugging Face Spaces (Docker SDK)
├── .dockerignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Prerequisites

- Python 3.10 or 3.11
- A [Groq](https://console.groq.com/) API key (free tier works)
- A [Neon](https://neon.tech/) Postgres database (free tier works)

### Database Setup (run once in Neon SQL editor)

```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE research_history (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    topic        TEXT NOT NULL,
    final_report TEXT,
    logs         JSONB,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🖥️ Running Locally in VS Code

### 1. Clone / copy the project
```bash
cd your-projects-folder
# project folder is already here
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your `.env` file
Edit `.env` in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
NEON_DATABASE_URL=your_DATABASE_URL_here

```

### 5. Run the server
```bash
python app.py
```


You should see the login screen. Sign up, then start researching!

---

## 🚀 Deploying to Hugging Face Spaces (Free, Docker)

### Step 1 — Create a new Space
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **Create new Space**
3. Give it a name (e.g. `recursive-research-agent`)
4. Select **Docker** as the SDK
5. Set visibility to **Public** (required for free tier)
6. Click **Create Space**

### Step 2 — Add your Secrets (Environment Variables)
In your Space → **Settings** → **Repository secrets**, add:
| Name | Value |
|------|-------|
| `GROQ_API_KEY` | Your Groq API key |
| `NEON_DATABASE_URL` | Your Neon connection string |


> ⚠️ Never put secrets in your code or commit your `.env` file.

### Step 3 — Push your code
```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit"

# Add Hugging Face remote
git remote add space https://huggingface.co/spaces/YOUR_HF_USERNAME/recursive-research-agent

# Push  (you'll be asked for HF username + token)
git push space main
```

> Get your HF token at: https://huggingface.co/settings/tokens  
> Use a token with **write** permission.

### Step 4 — Wait for build
Hugging Face will build the Docker container automatically (~2-3 minutes).  
Your app will be live at:  
`https://YOUR_HF_USERNAME-recursive-research-agent.hf.space`


---

##  Troubleshooting


**`psycopg2` install fails on Windows**  
→ Use `psycopg2-binary` (already in requirements.txt). If issues persist, install [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

**Hugging Face build fails**  
→ Check the **Logs** tab in your Space. Most common cause is a missing secret or a typo in `NEON_DATABASE_URL`.

**`401 Token expired or invalid`**  
→ Your JWT expired (24h). Just log out and log back in.