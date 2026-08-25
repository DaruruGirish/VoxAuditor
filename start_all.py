import subprocess
import os
import sys
import time

services = [
    {"name": "review-store",  "path": "services/review_store/main.py"},
    {"name": "vector-search", "path": "services/vector_search/main.py"},
    {"name": "analytics",     "path": "services/analytics/main.py"},
    {"name": "qa-agent",      "path": "services/qa_agent/main.py"},
    {"name": "gateway",       "path": "services/gateway/main.py"}
]

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

processes = []

python_exe = os.path.abspath(".venv/Scripts/python.exe")

print("Starting backend microservices...")

for svc in services:
    name = svc["name"]
    script_path = os.path.abspath(svc["path"])
    svc_dir = os.path.dirname(script_path)
    log_path = f"logs/{name}.log"
    log_file = open(log_path, "w", encoding="utf-8")
    
    print(f"  -> Starting {name} (cwd: {svc_dir})...")
    p = subprocess.Popen(
        [python_exe, "-u", "main.py"],
        cwd=svc_dir,
        stdout=log_file,
        stderr=subprocess.STDOUT,  # merge stderr into stdout
    )
    processes.append((name, p, log_file))
    time.sleep(1) # stagger startup

print("All backend services launched. Monitoring... Press Ctrl+C to terminate.")

try:
    while True:
        # Check if any process has exited
        for name, p, _ in processes:
            ret = p.poll()
            if ret is not None:
                print(f"[Warning] Service {name} has exited with code {ret}!")
        time.sleep(2)
except KeyboardInterrupt:
    print("Shutting down services...")
finally:
    for name, p, log_file in processes:
        print(f"Terminating {name}...")
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
        log_file.close()
    print("Shutdown complete.")
