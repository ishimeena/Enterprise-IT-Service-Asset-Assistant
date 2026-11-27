ASSETS = {
    "AST-1001": {
        "asset_tag": "AST-1001",
        "model": "Dell Latitude 5440",
        "assigned_to": "Nisha Rao",
        "department": "Finance",
        "status": "In Service",
    },
    "AST-1002": {
        "asset_tag": "AST-1002",
        "model": "HP EliteBook 840",
        "assigned_to": "Arjun Mehta",
        "department": "Engineering",
        "status": "In Service",
    },
    "AST-1003": {
        "asset_tag": "AST-1003",
        "model": "Lenovo ThinkPad T14",
        "assigned_to": "Maya Sen",
        "department": "Operations",
        "status": "Under Repair",
    },
    "AST-1004": {
        "asset_tag": "AST-1004",
        "model": "Dell Precision 3581",
        "assigned_to": "Kabir Das",
        "department": "Engineering",
        "status": "In Service",
    },
}

TICKETS = {
    "INC-2041": {
        "ticket_id": "INC-2041",
        "issue": "Laptop Display",
        "priority": "High",
        "status": "In Progress",
        "assigned_team": "Endpoint Support",
    },
    "INC-2042": {
        "ticket_id": "INC-2042",
        "issue": "VPN Access",
        "priority": "Medium",
        "status": "Waiting For User",
        "assigned_team": "Network Support",
    },
    "INC-2043": {
        "ticket_id": "INC-2043",
        "issue": "Printer Issue",
        "priority": "Low",
        "status": "Resolved",
        "assigned_team": "Workplace Technology",
    },
    "INC-2044": {
        "ticket_id": "INC-2044",
        "issue": "Email Access",
        "priority": "High",
        "status": "Open",
        "assigned_team": "Identity Support",
    },
}

SUPPORT_TEAMS = [
    "Endpoint Support",
    "Network Support",
    "Identity Support",
    "Workplace Technology",
]

_VALID_PRIORITIES = {"Low", "Medium", "High"}


def _validate_identifier(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def get_asset(asset_tag):
    asset_tag = _validate_identifier(asset_tag, "asset_tag")
    asset = ASSETS.get(asset_tag)
    return asset.copy() if asset is not None else None


def get_ticket(ticket_id):
    ticket_id = _validate_identifier(ticket_id, "ticket_id")
    ticket = TICKETS.get(ticket_id)
    return ticket.copy() if ticket is not None else None


def list_support_teams():
    return SUPPORT_TEAMS.copy()


def prepare_incident_draft(asset_tag, issue_description, priority):
    asset_tag = _validate_identifier(asset_tag, "asset_tag")
    if not isinstance(issue_description, str) or not issue_description.strip():
        raise ValueError("issue_description must be a non-empty string")
    if not isinstance(priority, str) or not priority.strip():
        raise ValueError("priority must be Low, Medium, or High")

    normalized_priority = priority.strip().title()
    if normalized_priority not in _VALID_PRIORITIES:
        raise ValueError("priority must be Low, Medium, or High")

    asset = get_asset(asset_tag)
    if asset is None:
        raise ValueError(f"Unknown asset_tag: {asset_tag}")

    return {
        "asset_tag": asset_tag,
        "asset": asset,
        "issue_description": issue_description.strip(),
        "priority": normalized_priority,
        "status": "Draft",
    }
