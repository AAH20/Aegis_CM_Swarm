import os, time, requests

TARGET_URL = os.getenv("TARGET_BASE_URL", "http://target_arena:8000")

def send_log(msg, color="text-blue-400"):
    try: requests.post(f"{TARGET_URL}/log", json={"sender": "Blue Hive", "msg": msg, "color": color})
    except: pass

def main():
    print("[*] Blue Hive active.")
    time.sleep(5)
    send_log("IDS and WAF sensors calibrated. Monitoring telemetry baseline.")
    
    while True:
        try:
            state = requests.get(f"{TARGET_URL}/api/state").json()
            if state["snort_alerts"] > 0:
                send_log(f"SNORT IDS TRIGGERED: {state['snort_alerts']} anomalous packets detected!", "text-blue-300 font-bold")
            if state["waf_blocks"] > 0:
                send_log(f"WAF ALERT: {state['waf_blocks']} malicious payloads blocked.", "text-blue-300 font-bold")
            if state["auth_failures"] > 100:
                send_log(f"AUTH ANOMALY: Mass authentication failures detected.", "text-blue-300 font-bold")
        except: pass
        time.sleep(3)

if __name__ == "__main__":
    main()