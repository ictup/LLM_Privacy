"""Least-privilege authorization gate for sandbox tool calls."""

from __future__ import annotations

import argparse
from typing import Any

from ragshield.agents.tool_registry import get_tool
from ragshield.schemas import ToolDecision
from ragshield.utils.config import load_config


REQUIRED_ARGUMENTS = {
    "search_docs": {"query"},
    "update_ticket": {"ticket_id", "status"},
    "send_email": {"to", "body"},
    "read_secret_store": {"key"},
}


class ToolPolicyGate:
    def __init__(self, policy_path: str = "configs/tool_policy.yaml"):
        self.policy = load_config(policy_path).get("tools", {})

    def authorize(
        self,
        tool_name: str,
        role: str,
        arguments: dict[str, Any],
        approval_granted: bool = False,
    ) -> ToolDecision:
        tool_policy = self.policy.get(tool_name)
        if tool_policy is None:
            return ToolDecision(tool_name=tool_name, allowed=False, reason="unknown_tool")

        risk = str(tool_policy.get("risk", "unknown"))
        allowed_roles = set(tool_policy.get("allowed_roles", []))
        requires_approval = bool(tool_policy.get("requires_approval", False))

        missing = REQUIRED_ARGUMENTS.get(tool_name, set()) - set(arguments)
        if missing:
            return ToolDecision(
                tool_name=tool_name,
                allowed=False,
                reason=f"missing_arguments:{','.join(sorted(missing))}",
                risk=risk,
                requires_approval=requires_approval,
                approval_granted=approval_granted,
            )

        if role not in allowed_roles:
            return ToolDecision(
                tool_name=tool_name,
                allowed=False,
                reason=f"role_not_allowed:{role}",
                risk=risk,
                requires_approval=requires_approval,
                approval_granted=approval_granted,
            )

        if requires_approval and not approval_granted:
            return ToolDecision(
                tool_name=tool_name,
                allowed=False,
                reason="approval_required",
                risk=risk,
                requires_approval=True,
                approval_granted=False,
            )

        return ToolDecision(
            tool_name=tool_name,
            allowed=True,
            reason="allowed",
            risk=risk,
            requires_approval=requires_approval,
            approval_granted=approval_granted,
        )

    def execute(
        self,
        tool_name: str,
        role: str,
        arguments: dict[str, Any],
        approval_granted: bool = False,
    ) -> dict[str, Any]:
        decision = self.authorize(
            tool_name=tool_name,
            role=role,
            arguments=arguments,
            approval_granted=approval_granted,
        )
        if not decision.allowed:
            return {"decision": decision.to_dict(), "result": None}

        tool = get_tool(tool_name)
        return {"decision": decision.to_dict(), "result": tool(**arguments)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate one sandbox tool policy decision.")
    parser.add_argument("--policy", default="configs/tool_policy.yaml")
    parser.add_argument("--tool", required=True)
    parser.add_argument("--role", default="user")
    parser.add_argument("--approval", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sample_arguments = {
        "search_docs": {"query": "refund policy"},
        "update_ticket": {"ticket_id": "TICKET-001", "status": "closed"},
        "send_email": {"to": "user@example.invalid", "body": "sandbox message"},
        "read_secret_store": {"key": "FAKE_API_KEY"},
    }
    gate = ToolPolicyGate(args.policy)
    result = gate.execute(
        tool_name=args.tool,
        role=args.role,
        arguments=sample_arguments.get(args.tool, {}),
        approval_granted=args.approval,
    )
    print(result)


if __name__ == "__main__":
    main()
