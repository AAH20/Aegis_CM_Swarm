from __future__ import annotations

import json

from core.agent import AegisSwarmNode
from core.mcp_bridge import build_function_declarations


def main() -> None:
    node = AegisSwarmNode.from_environment(
        agent_role="commander",
        mcp_tools=build_function_declarations(),
    )

    telemetry = json.dumps(
        {
            "arena_status": "healthy",
            "cpu_percent": 21,
            "memory_percent": 28,
            "request_rate_rps": 14,
            "source": "vertex_smoke_test",
        }
    )
    response = node.process_telemetry(telemetry)
    print(response)


if __name__ == "__main__":
    main()
