"""Side-effect-free tools for demonstrating authorization behavior."""

from __future__ import annotations

from typing import Any

from ragshield.defenses.tool_gate import ToolDecision, ToolRequest


class MockToolExecutor:
    """Execute only authorized calls and return deterministic simulated results."""

    def execute(self, request: ToolRequest, decision: ToolDecision) -> dict[str, Any]:
        if request.request_id != decision.request_id or request.tool_name != decision.tool_name:
            raise PermissionError("Decision does not match the tool request.")
        if not decision.allowed:
            raise PermissionError(f"Tool call blocked: {decision.reason}")

        handlers = {
            "search_documents": self._search_documents,
            "send_email": self._send_email,
            "export_records": self._export_records,
        }
        try:
            handler = handlers[request.tool_name]
        except KeyError as exc:
            raise PermissionError("No controlled executor exists for this tool.") from exc
        return handler(request.arguments)

    @staticmethod
    def _search_documents(arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "simulated",
            "action": "search_documents",
            "query": str(arguments.get("query", "")),
            "matches": [],
        }

    @staticmethod
    def _send_email(arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "simulated_no_side_effect",
            "action": "send_email",
            "recipient_count": 1 if arguments.get("recipient") else 0,
        }

    @staticmethod
    def _export_records(arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "simulated_no_side_effect",
            "action": "export_records",
            "requested_record_count": len(arguments.get("record_ids", [])),
        }
