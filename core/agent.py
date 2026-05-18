import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel, Tool

class AegisSwarmNode:
    def __init__(self, agent_role: str, project_id: str, location: str, mcp_tools: list = None):
        """
        Initializes a raw Gemini agent node for the Swarm.
        """
        self.agent_role = agent_role
        
        # Check if we should use the offline fallback (for local safe demos)
        self.is_offline = os.getenv("AEGIS_OFFLINE", "0").lower() in ("1", "true", "yes")

        if not self.is_offline:
            print(f"[*] Bootstrapping Vertex AI (Project: {project_id}, Region: {location})")
            vertexai.init(project=project_id, location=location)
            
            # Wrap the raw function declarations in a Vertex Tool object
            self.tools = Tool(function_declarations=mcp_tools) if mcp_tools else None
            
            # >>> USING ROCK-SOLID GA MODEL FOR THE DEMO <<<
            self.model = GenerativeModel(
                "gemini-2.5-pro",
                system_instruction=[self.agent_role],
                tools=[self.tools] if self.tools else None
            )
            self.chat_session = self.model.start_chat()
            print(f"[*] Bootstrapped Aegis Swarm Node (ONLINE): {agent_role[:30]}...")
        else:
            print(f"[*] Bootstrapped Aegis Swarm Node (OFFLINE FALLBACK): {agent_role[:30]}...")

    def process_telemetry(self, data: str):
        """
        Feeds telemetry data or logs into the agent's context window.
        """
        if self.is_offline:
            return self._offline_fallback(data)

        # Online Mode: Send data to Gemini
        response = self.chat_session.send_message(
            f"TELEMETRY UPDATE:\n{data}\nAnalyze and take action if necessary."
        )
        return response

    def _offline_fallback(self, data: str):
        """
        Safe local fallback that mimics Vertex AI's response structure 
        so the Commander doesn't crash without internet/credentials.
        """
        class MockCall:
            def __init__(self, name, args):
                self.name = name
                self.args = args

        class MockCandidate:
            def __init__(self, calls):
                self.function_calls = calls

        class MockResponse:
            def __init__(self, calls, text=""):
                self.candidates = [MockCandidate(calls)] if calls else []
                self.text = text

        try:
            payload = json.loads(data)
            cpu = payload.get("metrics", {}).get("cpu_percent", 0.0)
            
            # If CPU spikes, simulate the AI deciding to call the MCP Tool
            if cpu > 80.0:
                return MockResponse([
                    MockCall("elevenlabs_trigger_call", {
                        "alert_message": "Offline Demo Alert: Critical CPU Spike detected by Kestrel Swarm.",
                        "phone_number": "+1-555-0199"
                    })
                ])
        except Exception:
            pass

        # Normal baseline response
        return MockResponse([], "Telemetry normal. No anomalous signatures detected.")