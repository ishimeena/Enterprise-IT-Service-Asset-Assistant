import json
import re

from .config import MAX_AGENT_STEPS
from .knowledge import search_it_guide
from .ollama_client import generate
from .tools import get_asset, get_ticket, list_support_teams, prepare_incident_draft

SYSTEM_PROMPT = """You are an enterprise IT service asset assistant.
Use only the supplied tool results and the IT operations guide; do not invent facts.
Choose an allowed tool when it can answer the request. After observing a tool result,
either call another allowed tool if needed or return a concise answer.
For incident drafts, do not invent missing asset tags, issue descriptions, or priorities;
ask the user for any missing required information.
Return exactly one JSON object: either {"tool": "tool_name", "arguments": {...}}
or {"answer": "final response"}."""

TOOL_SCHEMAS = [
    {
        "name": "get_asset",
        "description": "Look up a fictional enterprise asset by asset tag.",
        "parameters": {"type": "object", "properties": {"asset_tag": {"type": "string"}}, "required": ["asset_tag"]},
    },
    {
        "name": "get_ticket",
        "description": "Look up a fictional incident ticket by ticket ID.",
        "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]},
    },
    {
        "name": "search_it_guide",
        "description": "Search the IT operations guide for policy and troubleshooting information.",
        "parameters": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
    },
    {
        "name": "list_support_teams",
        "description": "List the available IT support teams.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "prepare_incident_draft",
        "description": "Prepare, but do not submit, an incident draft for a known asset.",
        "parameters": {
            "type": "object",
            "properties": {
                "asset_tag": {"type": "string"},
                "issue_description": {"type": "string"},
                "priority": {"type": "string", "enum": ["Low", "Medium", "High"]},
            },
            "required": ["asset_tag", "issue_description", "priority"],
        },
    },
]

TOOL_DISPATCHER = {
    "get_asset": get_asset,
    "get_ticket": get_ticket,
    "search_it_guide": search_it_guide,
    "list_support_teams": list_support_teams,
    "prepare_incident_draft": prepare_incident_draft,
}
TOOL_ALLOWLIST = frozenset(TOOL_DISPATCHER)


def _route_request(question):
    if re.search(r"\b(?:draft|prepare)\b.*\b(?:incident|ticket)\b|\b(?:incident|ticket)\b.*\b(?:draft|prepare)\b", question, re.I):
        return {"tool": "prepare_incident_draft", "arguments": None}

    if re.search(r"\bsupport teams?\b|\bteams available\b", question, re.I):
        return {"tool": "list_support_teams", "arguments": {}}

    match = re.search(r"\bAST-\d{4}\b", question, re.I)
    if match:
        return {"tool": "get_asset", "arguments": {"asset_tag": match.group(0).upper()}}

    match = re.search(r"\bINC-\d{4}\b", question, re.I)
    if match:
        return {"tool": "get_ticket", "arguments": {"ticket_id": match.group(0).upper()}}

    if re.search(r"\b(?:policy|vpn|escalation|priority)\b", question, re.I):
        return {"tool": "search_it_guide", "arguments": {"question": question}}
    return None


def _dispatch_tool(name, arguments):
    if name not in TOOL_ALLOWLIST:
        raise ValueError(f"Tool is not allowed: {name}")
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object")

    schema = next(schema for schema in TOOL_SCHEMAS if schema["name"] == name)
    required = schema["parameters"]["required"]
    properties = schema["parameters"]["properties"]
    missing = [key for key in required if key not in arguments]
    unexpected = [key for key in arguments if key not in properties]
    if missing or unexpected:
        raise ValueError(f"Invalid arguments for tool {name}: missing={missing}, unexpected={unexpected}")
    return TOOL_DISPATCHER[name](**arguments)


def _parse_action(response):
    text = response.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        action = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The agent returned invalid JSON") from exc
    if not isinstance(action, dict):
        raise RuntimeError("The agent response must be a JSON object")

    answer = action.get("answer")
    if isinstance(answer, str) and answer.strip():
        return {"answer": answer.strip()}

    tool, arguments = action.get("tool"), action.get("arguments")
    if not isinstance(tool, str) or not isinstance(arguments, dict):
        raise RuntimeError("The agent response must contain an answer or a tool call")
    if tool not in TOOL_ALLOWLIST:
        raise RuntimeError(f"The agent requested a disallowed tool: {tool}")
    return {"tool": tool, "arguments": arguments}


def _make_prompt(question, trace, required_tool=None):
    route_instruction = ""
    if required_tool:
        route_instruction = f"\nUse {required_tool} only if all required information is present; otherwise ask for missing information."
    return (
        f"{SYSTEM_PROMPT}\n"
        f"Available tool schemas: {json.dumps(TOOL_SCHEMAS)}\n"
        f"{route_instruction}\n"
        f"User request: {json.dumps(question)}\n"
        f"Plan-Act-Observe trace so far: {json.dumps(trace, ensure_ascii=False)}\n"
        "Return the next tool call or the final answer as the required JSON object."
    )


def run_agent(question):
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")
    if not isinstance(MAX_AGENT_STEPS, int) or MAX_AGENT_STEPS < 1:
        raise ValueError("MAX_AGENT_STEPS must be a positive integer")

    question = question.strip()
    route = _route_request(question)
    trace = []
    last_result = None

    for step in range(1, MAX_AGENT_STEPS + 1):
        if step == 1 and route and route["arguments"] is not None:
            action = route
        else:
            required_tool = route["tool"] if step == 1 and route else None
            action = _parse_action(generate(_make_prompt(question, trace, required_tool)))
            if required_tool and "tool" in action and action["tool"] != required_tool:
                raise RuntimeError(f"The request must be handled by {required_tool}")

        if "answer" in action:
            trace.append({"step": step, "action": "answer", "answer": action["answer"]})
            return {"answer": action["answer"], "trace": trace, "steps": step}

        last_result = _dispatch_tool(action["tool"], action["arguments"])
        trace.append({"step": step, "action": "tool", "tool": action["tool"], "result": last_result})

    answer = "Maximum agent steps reached. Latest tool result: " + json.dumps(last_result, ensure_ascii=False)
    return {"answer": answer, "trace": trace, "steps": MAX_AGENT_STEPS}