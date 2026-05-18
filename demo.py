import os

from core.agent import AegisSwarmNode
from core.mcp_bridge import build_function_declarations


def main() -> None:
    offline = os.getenv("AEGIS_OFFLINE", "1").lower() in {"1", "true", "yes", "on"}
    node = AegisSwarmNode.from_environment(
        agent_role="commander",
        mcp_tools=build_function_declarations(),
        offline=offline,
    )

    telemetry = "{" \
        '"arena_status": "healthy", "cpu_percent": 21, "memory_percent": 28, "request_rate_rps": 14' \
        "}"
    response = node.process_telemetry(telemetry)
    print(response)


if __name__ == "__main__":
    main()