"""Batch teacher inference runner using local Ollama (phi3.5:latest).

Strict teacher inference specifications:
- Model: phi3.5:latest (3.8B parameters, Q4_0)
- Parameters: temperature 0, seed 42, format="json"
- Template: prompts/teacher_prompt.txt
- Checkpointed and resumable: raw teacher responses saved incrementally in shards.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Set

DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
PROMPT_TEMPLATE_PATH = "prompts/teacher_prompt.txt"
COMMANDS_PATH = "cloud_assignment/data/commands_pool.jsonl"
DEFAULT_SHARD_DIR = "data/teacher_shards"
DEFAULT_SHARD_SIZE = 500


def load_prompt_template(path: str = PROMPT_TEMPLATE_PATH) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def query_ollama(
    prompt: str,
    model: str = "phi3.5:latest",
    ollama_url: str = DEFAULT_OLLAMA_URL,
    timeout: int = 60,
) -> Dict[str, Any]:
    """Execute strict inference against local Ollama instance."""
    url = f"{ollama_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0,
            "seed": 42,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_existing_processed_ids(shard_dir: str) -> Set[str]:
    """Scan existing shard files to support resuming runs without duplicate inferences."""
    processed = set()
    if not os.path.exists(shard_dir):
        return processed
    for fname in os.listdir(shard_dir):
        if fname.endswith(".jsonl"):
            fpath = os.path.join(shard_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        if "id" in rec:
                            processed.add(str(rec["id"]))
                    except (json.JSONDecodeError, ValueError):
                        continue
    return processed


def run_distillation(
    commands_path: str = COMMANDS_PATH,
    shard_dir: str = DEFAULT_SHARD_DIR,
    shard_size: int = DEFAULT_SHARD_SIZE,
    model: str = "phi3.5:latest",
    ollama_url: str = DEFAULT_OLLAMA_URL,
    limit: Optional[int] = None,
) -> List[str]:
    """Run batch distillation over commands pool with sharded checkpointing."""
    os.makedirs(shard_dir, exist_ok=True)
    template = load_prompt_template()

    # Load commands
    commands: List[Dict[str, str]] = []
    with open(commands_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                commands.append(json.loads(line))

    if limit is not None and limit > 0:
        commands = commands[:limit]

    already_processed = get_existing_processed_ids(shard_dir)
    pending_commands = [c for c in commands if str(c["id"]) not in already_processed]

    print("=" * 60)
    print("Teacher Knowledge Distillation Runner (phi3.5:latest)")
    print("=" * 60)
    print(f"Total commands in scope:  {len(commands)}")
    print(f"Already completed:        {len(already_processed)}")
    print(f"Pending execution:        {len(pending_commands)}")
    print(f"Shard directory:          {shard_dir}")
    print(f"Ollama endpoint:          {ollama_url}")
    print("Inference settings:       temperature=0, seed=42, format=json")
    print("=" * 60)

    if not pending_commands:
        print("All commands in scope are already distilled.")
        return sorted([os.path.join(shard_dir, f) for f in os.listdir(shard_dir) if f.endswith(".jsonl")])

    # Determine current shard index
    existing_shards = [f for f in os.listdir(shard_dir) if f.startswith("shard-") and f.endswith(".jsonl")]
    shard_idx = len(existing_shards)
    current_shard_path = os.path.join(shard_dir, f"shard-{shard_idx}.jsonl")
    current_shard_count = 0

    shard_files: List[str] = [os.path.join(shard_dir, f) for f in existing_shards]

    start_time = time.time()
    for idx, cmd in enumerate(pending_commands, 1):
        c_id = str(cmd["id"])
        c_text = str(cmd["text"])
        prompt = template.replace("{{command}}", c_text)

        t0 = time.time()
        try:
            resp = query_ollama(prompt, model=model, ollama_url=ollama_url)
            raw_response = resp.get("response", "")
        except Exception as e:
            print(f"[{idx}/{len(pending_commands)}] Error querying {c_id}: {e}", file=sys.stderr)
            raw_response = json.dumps({"error": str(e)})

        dt = time.time() - t0

        record = {
            "id": c_id,
            "raw_response": raw_response,
            "inference_time_sec": round(dt, 3),
        }

        # Write to shard
        with open(current_shard_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        current_shard_count += 1
        if current_shard_path not in shard_files:
            shard_files.append(current_shard_path)

        if idx % 10 == 0 or idx == len(pending_commands):
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            print(f"  Progress: {idx}/{len(pending_commands)} ({idx*100.0/len(pending_commands):.1f}%) | {rate:.2f} cmd/s | Last: {dt:.2f}s")

        # Roll shard if limit reached
        if current_shard_count >= shard_size:
            shard_idx += 1
            current_shard_path = os.path.join(shard_dir, f"shard-{shard_idx}.jsonl")
            current_shard_count = 0

    print(f"\nDistillation complete in {time.time() - start_time:.1f}s.")
    return sorted(list(set(shard_files)))


def main():
    parser = argparse.ArgumentParser(description="Run batch teacher inference with Ollama phi3.5:latest.")
    parser.add_argument("--commands", default=COMMANDS_PATH, help="Path to commands_pool.jsonl")
    parser.add_argument("--shard-dir", default=DEFAULT_SHARD_DIR, help="Output directory for teacher shards")
    parser.add_argument("--shard-size", type=int, default=DEFAULT_SHARD_SIZE, help="Number of records per shard")
    parser.add_argument("--model", default="phi3.5:latest", help="Ollama model name")
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Ollama host URL")
    parser.add_argument("--sample", type=int, default=None, help="Limit number of commands for testing")
    args = parser.parse_args()

    run_distillation(
        commands_path=args.commands,
        shard_dir=args.shard_dir,
        shard_size=args.shard_size,
        model=args.model,
        ollama_url=args.ollama_url,
        limit=args.sample,
    )


if __name__ == "__main__":
    main()
