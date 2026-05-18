import os, time, requests

TARGET_URL = os.getenv("TARGET_BASE_URL", "http://target_arena:8000")

def send_log(msg, color="text-red-400"):
    try: requests.post(f"{TARGET_URL}/log", json={"sender": "Red Hive", "msg": msg, "color": color})
    except: pass

def main():
    time.sleep(3)
    send_log("Swarm linked. Awaiting Purple Commander authorization...", "text-slate-400")
    
    while True:
        try:
            res = requests.get(f"{TARGET_URL}/simulation_status").json()
            if res.get("started"): break
        except: pass
        time.sleep(2)
        
    send_log("Authorization granted. Generating 8-Stage Kill Chain...", "text-red-500 font-bold")
    time.sleep(25) 
    
    attacks = [
        ("nmap", "Stage 1: Nmap Stealth Scan (Reconnaissance)"),
        ("sqli", "Stage 2: SQL Injection (Weaponization)"),
        ("brute_force", "Stage 3: Credential Stuffing (Delivery)"),
        ("crypto", "Stage 4: Cryptojacker Deployment (Exploitation)"),
        ("ransomware", "Stage 5: Ransomware Encryption (Installation)"),
        ("ddos", "Stage 6: Botnet DDoS (Command & Control)"),
        ("container_escape", "Stage 7: Container Privilege Escalation"),
        ("lateral_movement", "Stage 8: Subnet Lateral Movement (Objective)")
    ]
    
    for attack_id, desc in attacks:
        send_log(f"🔥 LAUNCHING: {desc}", "text-red-500 font-bold")
        try: requests.post(f"{TARGET_URL}/launch_attack", json={"attack_type": attack_id})
        except: pass
        time.sleep(35) 

if __name__ == "__main__":
    main()