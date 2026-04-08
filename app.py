import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from core.database import db_execute
from core.models   import SignupRequest, LoginRequest, ResearchRequest, ResearchResponse, AgentState
from core.auth     import hash_password, verify_password, create_access_token, get_current_user
from core.agent    import agent_app

# ── APP SETUP ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Recursive Research Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── FRONTEND ROUTE ────────────────────────────────────────────────────────────
@app.get("/")
def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ── AUTH ROUTES ───────────────────────────────────────────────────────────────
@app.post("/signup")
async def signup(req: SignupRequest):
    if "@" not in req.email or len(req.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Invalid email or password too short (min 6 chars)"
        )
    existing = db_execute(
        "SELECT id FROM users WHERE email = %s",
        (req.email,),
        fetch="one"
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered. Please login.")

    hashed = hash_password(req.password)
    user   = db_execute(
        "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id, email",
        (req.email, hashed),
        fetch="returning"
    )
    token = create_access_token(str(user["id"]), user["email"])
    return {"token": token, "email": user["email"], "id": str(user["id"])}


@app.post("/login")
async def login(req: LoginRequest):
    user = db_execute(
        "SELECT * FROM users WHERE email = %s",
        (req.email,),
        fetch="one"
    )
    if not user:
        raise HTTPException(status_code=401, detail="No account found with this email.")
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    token = create_access_token(str(user["id"]), user["email"])
    return {"token": token, "email": user["email"], "id": str(user["id"])}


# ── RESEARCH ROUTE ────────────────────────────────────────────────────────────
@app.post("/research", response_model=ResearchResponse)
async def run_research(
    request: ResearchRequest,
    current_user: dict = Depends(get_current_user)
):
    initial_state: AgentState = {
        "topic":        request.topic,
        "report_draft": "",
        "unknown_terms": [],
        "definitions":  {},
        "final_report": "",
        "thinking_log": []
    }
    result = agent_app.invoke(initial_state)

    history_row = db_execute(
        """
        INSERT INTO research_history (user_id, topic, final_report, logs)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (
            current_user["id"],
            request.topic,
            result["final_report"],
            json.dumps(result["thinking_log"])
        ),
        fetch="returning"
    )
    history_id = str(history_row["id"]) if history_row else None

    return ResearchResponse(
        logs=result["thinking_log"],
        final_report=result["final_report"],
        history_id=history_id
    )


# ── HISTORY ROUTES ────────────────────────────────────────────────────────────
@app.get("/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    rows = db_execute(
        """
        SELECT id, topic, created_at
        FROM research_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (current_user["id"],),
        fetch="all"
    )
    history = [
        {
            "id":         str(row["id"]),
            "topic":      row["topic"],
            "created_at": row["created_at"].isoformat()
        }
        for row in (rows or [])
    ]
    return {"history": history}


@app.get("/history/{history_id}")
async def get_history_item(
    history_id: str,
    current_user: dict = Depends(get_current_user)
):
    row = db_execute(
        "SELECT * FROM research_history WHERE id = %s AND user_id = %s",
        (history_id, current_user["id"]),
        fetch="one"
    )
    if not row:
        raise HTTPException(status_code=404, detail="History item not found.")

    logs = row["logs"]
    if isinstance(logs, str):
        logs = json.loads(logs)

    return {
        "id":           str(row["id"]),
        "topic":        row["topic"],
        "final_report": row["final_report"],
        "logs":         logs,
        "created_at":   row["created_at"].isoformat()
    }


@app.delete("/history/{history_id}")
async def delete_history_item(
    history_id: str,
    current_user: dict = Depends(get_current_user)
):
    db_execute(
        "DELETE FROM research_history WHERE id = %s AND user_id = %s",
        (history_id, current_user["id"])
    )
    return {"message": "Deleted successfully"}


# ── USER ACCOUNT ROUTE ────────────────────────────────────────────────────────
@app.delete("/user")
async def delete_user_account(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    db_execute("DELETE FROM research_history WHERE user_id = %s", (user_id,))
    db_execute("DELETE FROM users WHERE id = %s",                 (user_id,))
    return {"message": "Account and all associated data deleted successfully."}