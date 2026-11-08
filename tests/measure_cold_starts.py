#!/usr/bin/env python3
"""Measure 3 cold starts: delete all pods, observe S3 download in logs,
record time from pod creation to Ready, report each run and the median.
"""

import json
import subprocess
import time


def get_pod_ready_times():
    """Delete all pods in app namespace and measure time until 2 replicas are Ready."""
    # Delete all pods
    subprocess.run("kubectl delete pods -n app --all", shell=True, check=True, stdout=subprocess.DEVNULL)
    t_start = time.time()

    # Wait until both pods are 1/1 Ready
    running_pods = []
    while time.time() - t_start < 120:
        out = subprocess.check_output(
            "kubectl get pods -n app --no-headers", shell=True, text=True
        ).strip().split("\n")

        ready_count = 0
        running_pods = []
        for line in out:
            parts = line.split()
            if len(parts) >= 3 and parts[2] == "Running":
                running_pods.append(parts[0])
                if parts[1] == "1/1":
                    ready_count += 1

        if ready_count >= 2:
            break
        time.sleep(1)

    duration = time.time() - t_start
    return duration, running_pods


runs = []
print("Measuring 3 cold starts...")

for run_idx in range(1, 4):
    print(f"\n--- Run {run_idx}/3 ---")
    dur, pods = get_pod_ready_times()
    print(f"Run {run_idx} completed in {dur:.2f}s (Pods: {pods})")
    runs.append(dur)
    time.sleep(3)

# Capture log evidence of S3 download from one of the pods
log_evidence = subprocess.check_output(
    "kubectl logs -n app deploy/command-parser --tail 25", shell=True, text=True
)

median_time = sorted(runs)[1]

report = {
    "run_1_sec": round(runs[0], 2),
    "run_2_sec": round(runs[1], 2),
    "run_3_sec": round(runs[2], 2),
    "median_sec": round(median_time, 2),
    "log_evidence": log_evidence.strip(),
}

with open("results/cold_start_measurements.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

with open("results/cold_start_logs.txt", "w", encoding="utf-8") as f:
    f.write("=== Cold Start Measurements over 3 Runs ===\n")
    f.write(f"Run 1: {runs[0]:.2f}s\n")
    f.write(f"Run 2: {runs[1]:.2f}s\n")
    f.write(f"Run 3: {runs[2]:.2f}s\n")
    f.write(f"Median Cold-Start Time: {median_time:.2f}s\n\n")
    f.write("=== S3 Model Download Log Evidence ===\n")
    f.write(log_evidence)

print("\nSUCCESS: Cold start measurements recorded!")
print(f"Run 1: {runs[0]:.2f}s, Run 2: {runs[1]:.2f}s, Run 3: {runs[2]:.2f}s -> Median: {median_time:.2f}s")
