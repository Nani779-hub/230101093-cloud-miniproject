"""Generate predictions from a Pythia-70M model checkpoint for validation commands."""
import argparse
import hashlib
import json
import os

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    StoppingCriteria,
    StoppingCriteriaList,
)


class StopAtCloseBrace(StoppingCriteria):
    def __init__(self, tokenizer, prompt_len):
        self.tokenizer = tokenizer
        self.prompt_len = prompt_len

    def __call__(self, input_ids, scores, **kwargs):
        last_token = input_ids[0][-1].item()
        last_str = self.tokenizer.decode([last_token])
        return "}" in last_str


def verify_model_checksum(model_dir: str, sha256_file: str) -> bool:
    """Verify model.safetensors against model.sha256."""
    if not os.path.exists(sha256_file):
        raise FileNotFoundError(f"Required checksum file not found: {sha256_file}")

    with open(sha256_file, "r", encoding="utf-8") as f:
        line = f.readline().strip()
        if not line:
            raise ValueError(f"Checksum file is empty: {sha256_file}")
        expected_hash = line.split()[0]

    target_file = os.path.join(model_dir, "model.safetensors")
    if not os.path.exists(target_file):
        raise FileNotFoundError(f"Required model asset not found: {target_file}")

    hasher = hashlib.sha256()
    with open(target_file, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    computed_hash = hasher.hexdigest()

    if computed_hash.lower() != expected_hash.lower():
        raise ValueError(
            f"Checksum mismatch for {target_file}!\nExpected: {expected_hash}\nComputed: {computed_hash}"
        )

    print(f"Checksum verified: {computed_hash} matches {sha256_file}")
    return True


def generate_predictions(model_dir: str, input_file: str, output_file: str, max_new_tokens: int = 50) -> None:
    """Load model from model_dir and run greedy inference over commands."""
    required_assets = ["model.safetensors", "config.json", "tokenizer.json"]
    for asset in required_assets:
        p = os.path.join(model_dir, asset)
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required model asset not found: {p}")

    print(f"Loading model and tokenizer from {model_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir)
    model.eval()

    with open(input_file, "r", encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    print(f"Generating predictions for {len(items)} inputs...")

    with open(output_file, "w", encoding="utf-8") as out_f:
        for item in items:
            prompt = f"Command: {item['text']}\nJSON: "
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=256)
            prompt_len = inputs["input_ids"].shape[1]
            stopping_criteria = StoppingCriteriaList([StopAtCloseBrace(tokenizer, prompt_len)])

            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    stopping_criteria=stopping_criteria,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )

            decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
            if "JSON: " in decoded:
                prediction = decoded.split("JSON: ", 1)[1].strip()
            else:
                prediction = decoded.strip()

            out_f.write(json.dumps({"id": item["id"], "prediction": prediction}) + "\n")

    print(f"Saved {len(items)} predictions to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate predictions from Pythia-70M model")
    parser.add_argument("--model", default="models/v1", help="Path to model directory")
    parser.add_argument("--input", default="cloud_assignment/data/validation.jsonl", help="Path to input validation.jsonl")
    parser.add_argument("--output", default="results/student_v1_predictions.jsonl", help="Output predictions path")
    parser.add_argument("--verify-checksum", default="models/v1/model.sha256", help="Path to model.sha256")
    parser.add_argument("--max-new-tokens", type=int, default=50, help="Maximum new tokens per inference")
    args = parser.parse_args()

    if args.verify_checksum:
        verify_model_checksum(args.model, args.verify_checksum)

    generate_predictions(args.model, args.input, args.output, max_new_tokens=args.max_new_tokens)


if __name__ == "__main__":
    main()
