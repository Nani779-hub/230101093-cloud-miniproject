#!/usr/bin/env python3
"""
Clean teacher-generated data.

Reads all shard outputs from S3 (datasets/teacher/shard-*.jsonl),
removes bad records, deduplicates, and writes the cleaned dataset
to datasets/v1/train.jsonl with a SHA-256 checksum.

Bad records:
  (a) replies that are not valid JSON
  (b) replies whose keys are not exactly intent, date, time, place
  (c) replies whose intent is not one of the eight valid intents
  (d) replies with a slot value that is neither null nor text that appears in the command
  (e) duplicate commands (keep the one with the smallest id)
"""

import hashlib
import json
import os

import boto3

S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localhost:8333")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
BUCKET = os.environ.get("BUCKET", "datasets")

VALID_INTENTS = {
    "alarm_set", "alarm_query", "calendar_set", "calendar_query",
    "calendar_remove", "weather_query", "datetime_query", "recommendation_events",
}
REQUIRED_KEYS = {"intent", "date", "time", "place"}


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="us-east-1",
    )


def load_shards(s3):
    """Load all shard files from S3 with local fallback."""
    records = []
    try:
        response = s3.list_objects_v2(Bucket=BUCKET, Prefix="teacher/")
        if "Contents" in response:
            for obj in response["Contents"]:
                key = obj["Key"]
                if not key.endswith(".jsonl"):
                    continue
                print(f"  Loading s3://{BUCKET}/{key}...")
                data = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read().decode("utf-8")
                for line in data.strip().split("\n"):
                    if line.strip():
                        records.append(json.loads(line))
            if records:
                return records
    except Exception as e:
        print(f"S3 fetch failed ({e}). Trying local fallback...")

    # Fallback: look for local shard files
    local_dirs = [
        os.path.join(os.path.dirname(__file__), "..", "data", "teacher_shards"),
        os.path.join(os.path.dirname(__file__), "..", "data", "teacher"),
    ]
    for local_dir in local_dirs:
        if os.path.exists(local_dir):
            for fname in sorted(os.listdir(local_dir)):
                if fname.endswith(".jsonl"):
                    print(f"  Loading local file {fname}...")
                    with open(os.path.join(local_dir, fname), encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                records.append(json.loads(line))
            if records:
                return records
    return records


def clean_records(records):
    """Clean records and return (cleaned_records, stats)."""
    stats = {
        "input": len(records),
        "rejected_invalid_json": 0,
        "rejected_wrong_keys": 0,
        "rejected_bad_intent": 0,
        "rejected_bad_slot": 0,
        "duplicates": 0,
        "kept": 0,
    }

    valid = []
    for rec in records:
        teacher_raw = rec.get("teacher_raw", "")
        text = rec.get("text", "").lower()
        cmd_id = rec.get("id", "")

        # (a) Parse JSON
        try:
            parsed = json.loads(teacher_raw)
        except (json.JSONDecodeError, TypeError):
            stats["rejected_invalid_json"] += 1
            continue

        if not isinstance(parsed, dict):
            stats["rejected_invalid_json"] += 1
            continue

        # (b) Check keys
        if set(parsed.keys()) != REQUIRED_KEYS:
            stats["rejected_wrong_keys"] += 1
            continue

        # (c) Check intent
        if parsed["intent"] not in VALID_INTENTS:
            stats["rejected_bad_intent"] += 1
            continue

        # (d) Check slot values
        bad_slot = False
        for slot in ("date", "time", "place"):
            val = parsed[slot]
            if val is None:
                continue
            if not isinstance(val, str):
                bad_slot = True
                break
            # The slot value must appear in the command text
            if val.lower().strip() not in text:
                bad_slot = True
                break
        if bad_slot:
            stats["rejected_bad_slot"] += 1
            continue

        valid.append({
            "id": cmd_id,
            "text": rec["text"],
            "teacher_raw": teacher_raw,
        })

    # (e) Deduplicate: keep the one with the smallest id for each text
    seen_texts = {}
    deduped = []
    # Sort by id first so smallest id comes first
    valid.sort(key=lambda r: r["id"])
    for rec in valid:
        text_key = rec["text"].strip().lower()
        if text_key in seen_texts:
            stats["duplicates"] += 1
            continue
        seen_texts[text_key] = True
        deduped.append(rec)

    # Sort by id
    deduped.sort(key=lambda r: r["id"])
    stats["kept"] = len(deduped)

    return deduped, stats


def main():
    s3 = get_s3_client()

    print("Loading shard files...")
    records = load_shards(s3)
    print(f"Loaded {len(records)} total records from shards")

    print("Cleaning records...")
    cleaned, stats = clean_records(records)

    # Write train.jsonl
    output_lines = []
    for rec in cleaned:
        output_lines.append(json.dumps(rec, ensure_ascii=False))
    output_data = "\n".join(output_lines) + "\n"

    # Compute SHA-256
    sha256 = hashlib.sha256(output_data.encode("utf-8")).hexdigest()

    # Upload to S3
    try:
        s3.put_object(
            Bucket=BUCKET,
            Key="v1/train.jsonl",
            Body=output_data.encode("utf-8"),
            ContentType="application/jsonl",
        )
        s3.put_object(
            Bucket=BUCKET,
            Key="v1/train.sha256",
            Body=f"{sha256}  train.jsonl\n".encode("utf-8"),
            ContentType="text/plain",
        )
        print(f"Uploaded cleaned dataset to s3://{BUCKET}/v1/train.jsonl")
    except Exception as e:
        print(f"Warning: S3 upload failed ({e})")

    # Also save locally for training
    local_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(local_dir, exist_ok=True)
    with open(os.path.join(local_dir, "train.jsonl"), "w", encoding="utf-8") as f:
        f.write(output_data)
    with open(os.path.join(local_dir, "train.sha256"), "w", encoding="utf-8") as f:
        f.write(f"{sha256}  train.jsonl\n")

    print(f"\n{'=' * 50}")
    print("Cleaning Report")
    print(f"{'=' * 50}")
    print(f"Input records:              {stats['input']}")
    print(f"(a) Invalid JSON:           {stats['rejected_invalid_json']}")
    print(f"(b) Wrong keys:             {stats['rejected_wrong_keys']}")
    print(f"(c) Bad intent:             {stats['rejected_bad_intent']}")
    print(f"(d) Bad slot value:         {stats['rejected_bad_slot']}")
    print(f"(e) Duplicates removed:     {stats['duplicates']}")
    print(f"Records kept:               {stats['kept']}")
    print(f"{'=' * 50}")
    print(f"Verification: {stats['input']} = {stats['rejected_invalid_json']} + {stats['rejected_wrong_keys']} + {stats['rejected_bad_intent']} + {stats['rejected_bad_slot']} + {stats['duplicates']} + {stats['kept']}")
    total = (stats['rejected_invalid_json']
             + stats['rejected_wrong_keys']
             + stats['rejected_bad_intent']
             + stats['rejected_bad_slot']
             + stats['duplicates']
             + stats['kept'])
    print(f"Sum check: {total} == {stats['input']} → {'OK' if total == stats['input'] else 'MISMATCH!'}")
    print(f"\nSHA-256: {sha256}")
    print(f"Output: s3://{BUCKET}/v1/train.jsonl")

    # Save stats for report
    stats_path = os.path.join(os.path.dirname(__file__), "..", "results", "cleaning_stats.json")
    os.makedirs(os.path.dirname(stats_path), exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


if __name__ == "__main__":
    main()
