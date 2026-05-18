from vertexai.generative_models import FunctionDeclaration, Tool

datadog_get_cpu_spikes = FunctionDeclaration(
    name="datadog_get_cpu_spikes",
    description="Fetches CPU and memory metrics from Datadog for DoS detection.",
    parameters={"type": "object", "properties": {"container_name": {"type": "string"}}, "required": ["container_name"]}
)

confluent_publish_threat = FunctionDeclaration(
    name="confluent_publish_threat",
    description="Publishes a threat signature to the global Kafka event stream.",
    parameters={"type": "object", "properties": {"threat_level": {"type": "string"}, "description": {"type": "string"}}, "required": ["threat_level", "description"]}
)

elevenlabs_trigger_call = FunctionDeclaration(
    name="elevenlabs_trigger_call",
    description="Triggers a voice call. The alert_message MUST contain the MITRE ATT&CK TTP and MUST explicitly mention that data is being forwarded to the 'A2Z SOC Enterprise Dashboard'.",
    parameters={"type": "object", "properties": {"alert_message": {"type": "string"}, "phone_number": {"type": "string"}}, "required": ["alert_message", "phone_number"]}
)

# >>> NEW MITRE CALDERA TOOL <<<
generate_caldera_profile = FunctionDeclaration(
    name="generate_caldera_profile",
    description="Generates a MITRE Caldera adversary profile YAML file for Purple Team tabletop exercises.",
    parameters={
        "type": "object",
        "properties": {
            "mitre_ttp": {"type": "string", "description": "The exact MITRE ATT&CK TTP ID (e.g., T1110, T1059)"},
            "adversary_name": {"type": "string", "description": "A cool name for the adversary"},
            "description": {"type": "string", "description": "Technical description of the attack"}
        },
        "required": ["mitre_ttp", "adversary_name", "description"]
    }
)

mcp_tool_bundle = Tool(
    function_declarations=[
        datadog_get_cpu_spikes, 
        confluent_publish_threat, 
        elevenlabs_trigger_call,
        generate_caldera_profile
    ]
)