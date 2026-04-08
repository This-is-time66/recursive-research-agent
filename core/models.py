from pydantic import BaseModel
from typing import List, Optional, TypedDict


# ── LANGGRAPH STATE ───────────────────────────────────────────────────────────
class AgentState(TypedDict):
    topic: str
    report_draft: str
    unknown_terms: List[str]
    definitions: dict
    final_report: str
    thinking_log: List[str]


# ── REQUEST / RESPONSE SCHEMAS ────────────────────────────────────────────────
class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ResearchRequest(BaseModel):
    topic: str


class ResearchResponse(BaseModel):
    logs: List[str]
    final_report: str
    history_id: Optional[str] = None