import os
import json
import time
import re
from groq import Groq
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from core.models import AgentState

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client  = Groq(api_key=GROQ_API_KEY)


# ── AGENT NODES ───────────────────────────────────────────────────────────────

def research_topic(state: AgentState):
    prompt = (
        f"Write a detailed 250-word research report on {state['topic']}. "
        "Do not include definitions yet. Focus on high-level technical accuracy."
    )
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    draft = response.choices[0].message.content
    return {
        "report_draft": draft,
        "thinking_log": state["thinking_log"] + ["Generated initial 250-word report draft."]
    }


def identify_terms(state: AgentState):
    prompt = (
        "Analyze the following text and identify 3 to 5 uncommon, technical, or jargon terms. "
        "Return ONLY a JSON object with key 'terms' containing a list of strings.\n\n"
        f"Text: {state['report_draft']}"
    )
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    data  = json.loads(response.choices[0].message.content)
    terms = data.get("terms", []) or list(data.values())[0]
    log   = state["thinking_log"] + [f"Identified {len(terms)} technical terms: {', '.join(terms)}"]
    return {"unknown_terms": terms, "thinking_log": log}


def define_terms(state: AgentState):
    defs = {}
    log  = list(state["thinking_log"])
    for term in state["unknown_terms"]:
        prompt = (
            f"Provide a one-sentence, clear definition for the term '{term}' "
            f"in the context of {state['topic']}. Be precise and informative."
        )
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        defs[term] = response.choices[0].message.content.strip()
        log.append(f"Defined '{term}' successfully.")
        time.sleep(0.3)
    log.append("All terms defined. Resuming main thread.")
    return {"definitions": defs, "thinking_log": log}


def compile_report(state: AgentState):
    final = state["report_draft"]
    for term, definition in state["definitions"].items():
        badge = (
            f'<span class="term">{term}</span> '
            f'<span class="bracket">{definition}</span>'
        )
        final = re.sub(re.escape(term), badge, final, count=1, flags=re.IGNORECASE)
    paragraphs  = [f"<p>{p.strip()}</p>" for p in final.split("\n\n") if p.strip()]
    html_report = "\n".join(paragraphs)
    log = state["thinking_log"] + ["Compiled final report with inline definitions."]
    return {"final_report": html_report, "thinking_log": log}


# ── LANGGRAPH PIPELINE ────────────────────────────────────────────────────────

def build_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("researcher", research_topic)
    workflow.add_node("analyzer",   identify_terms)
    workflow.add_node("definer",    define_terms)
    workflow.add_node("compiler",   compile_report)
    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "analyzer")
    workflow.add_edge("analyzer",   "definer")
    workflow.add_edge("definer",    "compiler")
    workflow.add_edge("compiler",   END)
    return workflow.compile()


# Singleton — imported and reused in app.py
agent_app = build_agent()