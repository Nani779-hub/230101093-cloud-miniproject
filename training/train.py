#!/usr/bin/env python3
"""
Fine-tune EleutherAI/pythia-70m on teacher-generated data (sequence-level distillation).

Usage:
  python train.py                     # Train on first 1500 records
  python train.py --subset 50         # Train on first 50 records (for testing)

Reads hyperparameters from training/config.yaml.
Saves model and tokenizer to training/output/v1/ (or v2/).
Logs per-epoch loss to training/loss.csv.
"""

import argparse
import csv
import hashlib
import json
import os

import yaml
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)


def load_config(config_path=None):
    if config_path is None:
        config_path = os.path.join(SCRIPT_DIR, "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {
        "model": {"base_model": "EleutherAI/pythia-70m", "max_records": 1500},
        "seed": 42,
        "model_name": "EleutherAI/pythia-70m",
        "max_sequence_length": 64,
        "batch_size": 16,
        "learning_rate": 5e-5,
        "epochs": 3,
    }


def format_training_prompt(text, label):
    """Format input text and label dictionary into causal training prompt."""
    if isinstance(label, dict):
        raw = json.dumps(label)
    else:
        raw = str(label)
    return f"Command: {text}\nJSON: {raw}"


def load_dataset(file_path, max_records=None):
    """Load JSONL dataset up to max_records."""
    records = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
                    if max_records and len(records) >= max_records:
                        break
    return records


def record_loss(csv_path, loss_log):
    """Save epoch loss logs to CSV."""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", "loss"])
        writer.writeheader()
        for row in loss_log:
            loss_val = row.get("loss")
            if isinstance(loss_val, float):
                formatted_loss = f"{loss_val:.4f}"
            else:
                formatted_loss = loss_val
            writer.writerow({"epoch": row.get("epoch"), "loss": formatted_loss})


class CommandDataset(Dataset):
    """Dataset for command-parsing fine-tuning."""

    def __init__(self, records, tokenizer, max_length):
        self.examples = []
        for rec in records:
            text = rec["text"]
            teacher_raw = rec.get("teacher_raw")
            if teacher_raw is None:
                teacher_raw = {k: rec.get(k) for k in ["intent", "date", "time", "place"] if k in rec}
            prompt = format_training_prompt(text, teacher_raw)
            encoding = tokenizer(
                prompt,
                truncation=True,
                max_length=max_length,
                padding="max_length",
                return_tensors="pt",
            )
            input_ids = encoding["input_ids"].squeeze(0)
            attention_mask = encoding["attention_mask"].squeeze(0)
            # Labels are the same as input_ids for causal LM
            labels = input_ids.clone()
            # Mask padding tokens in labels
            labels[attention_mask == 0] = -100
            self.examples.append({
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels,
            })

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]


def compute_checksum(directory):
    """Compute SHA-256 of all model files in a directory."""
    h = hashlib.sha256()
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        if os.path.isfile(fpath):
            with open(fpath, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    h.update(chunk)
    return h.hexdigest()


def train(config, subset=None, version="v1"):
    # Set seed for reproducibility
    seed = config["seed"]
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # Load data
    data_path = os.path.join(PROJECT_DIR, "data", "train.jsonl")
    max_records = subset if subset else config.get("max_train_records", 1500)
    records = load_dataset(data_path, max_records=max_records)
    print(f"Training on {len(records)} records (version: {version})")

    # Load model and tokenizer
    model_name = config["model_name"]
    print(f"Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float32)

    # Set pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.config.pad_token_id = model.config.eos_token_id

    # Create dataset
    max_length = config["max_sequence_length"]
    dataset = CommandDataset(records, tokenizer, max_length)
    batch_size = config["batch_size"]
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Training setup
    lr = config["learning_rate"]
    epochs = config["epochs"] if version == "v1" else config.get("epochs_v2", config["epochs"] + 2)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)

    total_steps = len(dataloader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(0.1 * total_steps),
        num_training_steps=total_steps,
    )

    # Training loop
    model.train()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    loss_log = []
    print(f"Starting training: {epochs} epochs, lr={lr}, batch_size={batch_size}")
    for epoch in range(epochs):
        total_loss = 0
        num_batches = 0
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )
            loss = outputs.loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches
        loss_log.append({"epoch": epoch + 1, "loss": round(avg_loss, 6)})
        print(f"  Epoch {epoch + 1}/{epochs} - Loss: {avg_loss:.6f}")

    # Save loss.csv
    loss_csv_path = os.path.join(SCRIPT_DIR, "loss.csv")
    record_loss(loss_csv_path, loss_log)
    print(f"Saved loss log to {loss_csv_path}")

    # Save model
    output_dir = os.path.join(SCRIPT_DIR, "output", version)
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Saved model to {output_dir}")

    # Compute checksum
    checksum = compute_checksum(output_dir)
    checksum_path = os.path.join(output_dir, "model.sha256")
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  model\n")
    print(f"SHA-256: {checksum}")

    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Fine-tune Pythia-70M for command parsing")
    parser.add_argument("--subset", type=int, default=None, help="Train on first N records only")
    parser.add_argument("--version", default="v1", help="Model version (v1 or v2)")
    args = parser.parse_args()

    config = load_config()
    train(config, subset=args.subset, version=args.version)


if __name__ == "__main__":
    main()
