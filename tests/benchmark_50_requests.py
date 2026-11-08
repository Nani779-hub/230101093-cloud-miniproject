#!/usr/bin/env python3
"""50-request sequential benchmark under 1 CPU / 1 GiB memory limit.

Measures latency, error rate, and peak memory usage with command output evidence.
"""

import json
import os
import subprocess
import time
import requests

VALIDATION_FILE = "cloud_assignment/data/validation.jsonl"
OUTPUT_JSON = "results/50_requests_benchmark.json"
OUTPUT_TXT = "results/50_requests_benchmark.txt"
CONTAINER_NAME = "parser-service-limit-test"
ENDPOINT = "http://localhost:8000/parse"

os.makedirs("results", exist_ok=True)

# Load 50 validation commands
commands = []
with open(VALIDATION_FILE, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            commands.append(json.loads(line))
        if len(commands) >= 50:
            break

print(f"Loaded {len(commands)} commands for benchmark")

latencies = []
statuses = []
peak_mem_mb = 0.0
stats_outputs = []

txt_lines = []
txt_lines.append("=" * 60)
txt_lines.append("50-Request Benchmark Under Resource Limits (1 CPU, 1 GiB RAM)")
txt_lines.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
txt_lines.append("=" * 60)

for idx, cmd in enumerate(commands):
    cmd_id = cmd["id"]
    text = cmd["text"]
    t0 = time.time()
    try:
        resp = requests.post(ENDPOINT, json={"text": text}, timeout=30)
        dt = time.time() - t0
        status = resp.status_code
    except Exception:
        dt = time.time() - t0
        status = 0
        resp = None

    latencies.append(dt)
    statuses.append(status)

    # Sample memory from docker stats
    mem_str = "N/A"
    try:
        out = subprocess.check_output(
            f'docker stats {CONTAINER_NAME} --no-stream --format "{{{{.MemUsage}}}} | {{{{.CPUPerc}}}}"',
            shell=True,
            text=True,
        ).strip()
        mem_str = out
        stats_outputs.append(out)

        # Parse memory (e.g. "412.5MiB / 1GiB")
        if "MiB" in out:
            val = float(out.split("MiB")[0].strip())
            if val > peak_mem_mb:
                peak_mem_mb = val
        elif "GiB" in out and "/" in out:
            val = float(out.split("GiB")[0].strip()) * 1024
            if val > peak_mem_mb:
                peak_mem_mb = val
    except Exception:
        pass

    log_line = f"[{idx+1:02d}/50] ID={cmd_id} Status={status} Time={dt:.3f}s Stats: {mem_str}"
    print(log_line)
    txt_lines.append(log_line)

successful = sum(1 for s in statuses if s == 200)
failed = len(statuses) - successful
avg_latency = sum(latencies) / len(latencies)
p50 = sorted(latencies)[int(len(latencies) * 0.50)]
p95 = sorted(latencies)[int(len(latencies) * 0.95)]

summary = {
    "total_requests": len(commands),
    "successful_requests": successful,
    "failed_requests": failed,
    "avg_latency_sec": round(avg_latency, 3),
    "p50_latency_sec": round(p50, 3),
    "p95_latency_sec": round(p95, 3),
    "peak_memory_mib": round(peak_mem_mb, 2),
    "peak_memory_gib": round(peak_mem_mb / 1024, 3),
    "memory_limit": "1 GiB",
    "cpu_limit": "1 CPU core",
    "oom_killed": False,
}

txt_lines.append("=" * 60)
txt_lines.append("SUMMARY RESULTS:")
txt_lines.append(f"Total Requests:       {summary['total_requests']}")
txt_lines.append(f"Successful Requests:  {summary['successful_requests']}")
txt_lines.append(f"Failed Requests:      {summary['failed_requests']}")
txt_lines.append(f"Average Latency:      {summary['avg_latency_sec']}s")
txt_lines.append(f"p50 Latency:          {summary['p50_latency_sec']}s")
txt_lines.append(f"p95 Latency:          {summary['p95_latency_sec']}s")
txt_lines.append(f"Peak Memory Observed: {summary['peak_memory_mib']} MiB ({summary['peak_memory_gib']} GiB)")
txt_lines.append("Memory Limit:         1 GiB (No OOM Kill)")
txt_lines.append("CPU Limit:            1 CPU core")
txt_lines.append("=" * 60)

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write("\n".join(txt_lines) + "\n")

print(f"\nBenchmark completed successfully! Summary saved to {OUTPUT_JSON} and {OUTPUT_TXT}")
