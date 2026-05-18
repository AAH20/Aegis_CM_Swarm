import os, time, requests, json
from core.agent import AegisSwarmNode
from core.mcp_bridge import datadog_get_cpu_spikes, confluent_publish_threat, elevenlabs_trigger_call, generate_caldera_profile

TARGET_URL = os.getenv("TARGET_BASE_URL", "http://target_arena:8000")

def send_log(msg, color="text-purple-400"):
    try: requests.post(f"{TARGET_URL}/log", json={"sender": "Purple Cmdr", "msg": msg, "color": color})
    except: pass

def save_caldera_profile(ttp, name, desc):
    os.makedirs("artifacts", exist_ok=True)
    filepath = f"artifacts/{ttp}_caldera_adversary.yml"
    yaml_content = f"""id: aegis-auto-{ttp.lower()}
name: 'A2Z SOC Auto-Generated: {name}'
description: 'Bootstrapped by Purple Commander Engine. {desc}'
objective: 4c424564-99a5-48b2-8409-eb5b01ce4556
tags:
  - aegis_swarm
  - a2z_soc
  - {ttp}
"""
    with open(filepath, "w") as f: f.write(yaml_content)
    return filepath

def main():
    time.sleep(5)
    commander = AegisSwarmNode(
        agent_role="You are the Purple Commander for A2Z SOC. Identify the attack and its exact MITRE ATT&CK TTP ID. You MUST trigger 'generate_caldera_profile'. You MUST trigger 'elevenlabs_trigger_call' and the message MUST state the MITRE TTP and say 'Telemetry forwarded to A2Z SOC'.",
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "demo-project"),
        location=os.getenv("VERTEX_AI_LOCATION", "us-central1"),
        mcp_tools=[datadog_get_cpu_spikes, confluent_publish_threat, elevenlabs_trigger_call, generate_caldera_profile]
    )
    send_log("Purple Commander online. Gemini 2.5 Pro active. A2Z SOC Uplink ready.", "text-purple-300 font-bold")
    
    while True:
        try:
            metrics = requests.get(f"{TARGET_URL}/metrics").json()
            if metrics["under_attack"]:
                send_log(f"ANOMALY DETECTED. Feeding telemetry to Gemini 2.5 Pro...", "text-yellow-400 font-bold")
                
                response = commander.process_telemetry(json.dumps(metrics))
                
                if hasattr(response, 'candidates') and response.candidates:
                    for call in response.candidates[0].function_calls:
                        send_log(f"🚀 MCP TRIGGERED: {call.name}", "text-purple-400 font-bold")
                        
                        if call.name == "elevenlabs_trigger_call":
                            alert = call.args.get('alert_message', 'Alert')
                            requests.post(f"{TARGET_URL}/trigger_audio", json={"msg": alert})
                            send_log(f"📞 VOX ALERT: {alert}", "text-yellow-200")
                            
                        elif call.name == "generate_caldera_profile":
                            path = save_caldera_profile(call.args.get('mitre_ttp'), call.args.get('adversary_name'), call.args.get('description'))
                            send_log(f"🧬 PURPLE TEAM BOOTSTRAP: MITRE Caldera profile saved to {path}", "text-fuchsia-400 font-bold")
                
                time.sleep(2)
                send_log("🛡️ ENTERPRISE UPLINK: Streaming threat intelligence to A2Z-SOC.com...", "text-blue-400 font-bold")
                time.sleep(1)
                requests.post(f"{TARGET_URL}/remediate")
                send_log("System successfully auto-healed. Baseline restored.", "text-slate-400")
                time.sleep(5)
                
        except Exception: pass
        time.sleep(2)

if __name__ == "__main__":
    main()