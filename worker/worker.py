#!/usr/bin/env python3
"""
Sharded teacher-labelling worker.

Reads SHARD_INDEX (starting from 0) and SHARD_COUNT from environment variables.
Takes commands whose line number (0-based) leaves remainder SHARD_INDEX when
divided by SHARD_COUNT. Sends each to the teacher (Ollama phi3.5) and writes
results to object storage as datasets/teacher/shard-{SHARD_INDEX}.jsonl.
Supports resumption and periodic flushing to S3.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

import boto3

# ── Configuration from environment ──────────────────────────────────────────
SHARD_INDEX = int(os.environ.get("SHARD_INDEX", "0"))
SHARD_COUNT = int(os.environ.get("SHARD_COUNT", "2"))
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://host.k3d.internal:11434")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://seaweedfs.data.svc.cluster.local:8333")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "admin")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "admin")
BUCKET = os.environ.get("BUCKET", "datasets")
COMMANDS_KEY = os.environ.get("COMMANDS_KEY", "commands_pool.jsonl")
PROMPT_FILE = os.environ.get("PROMPT_FILE", "prompts/teacher_prompt.txt")

MODEL = "phi3.5"
TEMPERATURE = 0
SEED = 42
FLUSH_INTERVAL = 10  # write to S3 every 10 records


def load_prompt():
    """Load teacher prompt from file or use inline default."""
    prompt_paths = [
        PROMPT_FILE,
        os.path.join(os.path.dirname(__file__), "..", "prompts", "teacher_prompt.txt"),
        "/app/prompts/teacher_prompt.txt",
    ]
    for p in prompt_paths:
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return f.read().strip()
    return (
        'You are a command parser. Given a natural language command, extract the intent and slots.\n'
        'Output ONLY a single JSON object with exactly four keys: "intent", "date", "time", "place". '
        'No other text, no explanation, no markdown.\n'
        'The intent must be one of: alarm_set, alarm_query, calendar_set, calendar_query, '
        'calendar_remove, weather_query, datetime_query, recommendation_events.\n'
        'Slot rules:\n'
        '1. Copy the slot value EXACTLY as it appears in the command. Do NOT convert it.\n'
        '2. Copy the SHORTEST phrase that carries the meaning, WITHOUT words like "at", "on", "in", or "for".\n'
        '3. If the command does not mention a slot, set it to null. NEVER invent a value.\n\n'
        'Now parse the following command:'
    )


SYSTEM_PROMPT = load_prompt()


def get_s3_client():
    """Create boto3 S3 client for SeaweedFS."""
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="us-east-1",
    )


def load_commands_from_s3(s3):
    """Download commands_pool.jsonl from S3, with local fallback."""
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=COMMANDS_KEY)
        content = obj["Body"].read().decode("utf-8")
        commands = []
        for line in content.strip().split("\n"):
            if line.strip():
                commands.append(json.loads(line))
        return commands
    except Exception as e:
        print(f"S3 fetch failed ({e}), trying local file...", file=sys.stderr)
        local_paths = [
            os.path.join(os.path.dirname(__file__), "..", "data", "commands_pool.jsonl"),
            "/app/data/commands_pool.jsonl",
            "data/commands_pool.jsonl",
        ]
        for lp in local_paths:
            if os.path.exists(lp):
                commands = []
                with open(lp, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            commands.append(json.loads(line))
                return commands
        raise


def load_existing_shard(s3, output_key):
    """Load already processed records from S3 if shard exists (for resumption)."""
    results_map = {}
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=output_key)
        content = obj["Body"].read().decode("utf-8")
        for line in content.strip().split("\n"):
            if line.strip():
                rec = json.loads(line)
                results_map[rec["id"]] = rec
        print(f"Resuming: found {len(results_map)} existing records in s3://{BUCKET}/{output_key}")
    except Exception:
        pass
    return results_map


def query_teacher(text):
    """Send a command to the teacher model (Ollama phi3.5) and return the raw reply."""
    url = f"{OLLAMA_HOST}/api/generate"
    payload = json.dumps({
        "model": MODEL,
        "prompt": f"{SYSTEM_PROMPT}\nCommand: {text}",
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
            "seed": SEED,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "").strip()
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed ({e}), retrying...", file=sys.stderr)
            time.sleep(2)
    return ""


def flush_to_s3(s3, output_key, records_list):
    """Write records to S3."""
    output_data = "\n".join(json.dumps(r, ensure_ascii=False) for r in records_list) + "\n"
    s3.put_object(
        Bucket=BUCKET,
        Key=output_key,
        Body=output_data.encode("utf-8"),
        ContentType="application/jsonl",
    )


def main():
    print(f"Worker starting: SHARD_INDEX={SHARD_INDEX}, SHARD_COUNT={SHARD_COUNT}")
    print(f"Ollama host: {OLLAMA_HOST}")
    print(f"S3 endpoint: {S3_ENDPOINT}")

    s3 = get_s3_client()

    commands = load_commands_from_s3(s3)
    print(f"Loaded {len(commands)} commands total")

    my_commands = [
        cmd for i, cmd in enumerate(commands)
        if i % SHARD_COUNT == SHARD_INDEX
    ]
    print(f"This shard will process {len(my_commands)} commands")

    output_key = f"teacher/shard-{SHARD_INDEX}.jsonl"
    existing_records = load_existing_shard(s3, output_key)

    results = []
    processed_count = 0

    for idx, cmd in enumerate(my_commands):
        cmd_id = cmd["id"]
        text = cmd["text"]

        if cmd_id in existing_records:
            results.append(existing_records[cmd_id])
            continue

        t0 = time.time()
        teacher_raw = query_teacher(text)
        dt = time.time() - t0

        record = {
            "id": cmd_id,
            "text": text,
            "teacher_raw": teacher_raw,
        }
        results.append(record)
        processed_count += 1

        print(f"  [{idx + 1}/{len(my_commands)}] {cmd_id} ({dt:.2f}s): {teacher_raw[:50]}")
        sys.stdout.flush()

        if processed_count % FLUSH_INTERVAL == 0:
            flush_to_s3(s3, output_key, results)
            print(f"  [Checkpoint] Flushed {len(results)} records to s3://{BUCKET}/{output_key}")
            sys.stdout.flush()

    # Final write to S3
    flush_to_s3(s3, output_key, results)
    print(f"SUCCESS: Wrote all {len(results)} records to s3://{BUCKET}/{output_key}")


if __name__ == "__main__":
    main()
