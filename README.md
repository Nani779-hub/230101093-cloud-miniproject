# Cloud Computing Mini Project: Knowledge Distillation & Cloud-Native Deployment

**Course:** CS3081 Cloud Computing  
**Student Name:** Sabavat Sachith Naik  
**Roll Number:** 230101093  
**Hardware Environment:** Intel Core i5-1334U (10 cores), 16 GB RAM  
**Software Stack:** Python 3.11.9, Docker Desktop, k3d / k3s Kubernetes, SeaweedFS S3, FastAPI, Uvicorn, PyTorch (CPU-only), Hugging Face Transformers, Flake8, Pytest, Locust.

---

## 1. Overview & Architecture

This repository delivers an end-to-end, reproducible, cloud-native microservice architecture for natural language command parsing on the SLURP benchmark:

1. **Teacher Distillation (`prompts/teacher_prompt.txt`, `worker/worker.py`):**
   - 3,000 commands labelled by Phi-3.5-mini-instruct (3.8B parameters) via Ollama with fixed `temperature: 0` and `seed: 42`.
   - Modulo sharded across 2 concurrent worker jobs (`teacher-worker-0` and `teacher-worker-1`) in namespace `pipeline`, writing 1,500 commands each to `s3://datasets/teacher/shard-0.jsonl` and `shard-1.jsonl`.
2. **Data Cleaning & Accounting (`worker/clean.py`):**
   - Sanitizes raw teacher outputs against rules (a)-(e).
   - Strict identity verified: $3000 = 1032 \text{ (invalid JSON)} + 0 \text{ (wrong keys)} + 0 \text{ (bad intent)} + 46 \text{ (bad slot)} + 34 \text{ (duplicates)} + 1888 \text{ (kept)}$.
   - Kept dataset published to `s3://datasets/v1/train.jsonl` with SHA-256 `a6ba785ca8cc3ab5dfe853cd01371178ce265f383279cf176ba99463656ea6ad`.
3. **Student Model Fine-Tuning (`training/train.py`, `training/config.yaml`):**
   - Sequence-level distillation fine-tuning `EleutherAI/pythia-70m` on strictly the first 1,500 cleaned records.
   - Evaluated with `cloud_assignment/tools/score.py` on `validation.jsonl`:
     - Teacher: JSON Validity 70.0%, Intent 62.0%, Full Frame 33.0%
     - Untrained Pythia-70M: JSON Validity 0.0%, Full Frame 0.0%
     - Trained Student v1: JSON Validity 97.0% (>= 95% quality gate!), Full Frame 29.0% (>= 16.5% half of teacher).
   - Real epoch loss log saved in `training/loss.csv` (2.2158 down to 0.1716).
4. **Containerized Inference Service (`service/app.py`, `Dockerfile`):**
   - FastAPI microservice listening on port 8000 with endpoints `POST /parse`, `GET /healthz`, `GET /readyz`.
   - Injects response headers `X-Model-Version` and `X-Served-By`.
   - Downloads model weights dynamically from S3 on startup using Secret credentials (`s3-credentials`). Docker image contains 0 MB model weights and is 1.64 GB (under 2 GB ceiling).
   - Validates against `schema.json`; fault injection (`FAULT_INJECT=1`) returns HTTP 500 `{"error": "invalid_model_output"}`.
   - 50-request benchmark under limits (1 CPU, 1 GiB): peak memory 333.9 MiB, 0 OOM kills.
5. **Kubernetes Deployment, HPA, Scaling & Reliability (`k8s/`, `cluster/k3d.yaml`):**
   - Deployed on k3d cluster with Traefik Ingress routing `/parse` on port 8080.
   - HPA: min 1, max 2 replicas, target CPU 70%.
   - Rolling update v1 -> v2 -> v1 under load: 232 requests served across both versions with 0.0% downtime.
   - Pod recovery: deleted 1 pod under load; restored replica count in < 15s with only 0.625% transient errors (<= 2.0% limit).
   - Cold starts: Run 1 = 72.58s, Run 2 = 9.82s, Run 3 = 19.02s -> Median = 19.02s.
   - Load balancing: 2 Ready replicas served 51.8% vs 48.2% of requests (both >> 30%).
6. **Subnetting & Stateless NACLs (`network/subnets.md`, `network/nacl.json`):**
   - Subnets for `10.20.0.0/16`: app (`10.20.0.0/22`, 1,022 hosts), public (`10.20.4.0/24`, 254 hosts), data (`10.20.5.0/25`, 126 hosts), mgmt (`10.20.5.128/27`, 30 hosts).
   - Stateless NACL rules: 100% verified (6/6) with `cloud_assignment/tools/nacl_sim.py`.
7. **Reproducibility, Unit Tests & CI/CD (`Makefile`, `tests/`, `.github/workflows/ci.yml`):**
   - Flake8 linter clean (0 errors).
   - 23 unit tests passing in < 7s (`tests/test_cleaning_rules.py`, `tests/test_service_schema.py`, `tests/test_nacl_rules.py`).
   - GitHub Actions workflow stages: linting -> unit tests -> model evaluation (quality gate >= 95%) -> secret scanning (Gitleaks).
8. **Performance, Cost & Architectural Review (`results/`):**
   - Locust 2-minute load test (4 users): 113 requests, 110 successful, p50 = 2,800 ms, p95 = 9,000 ms, throughput 0.95 req/s.
   - Estimated cost: 2.39 INR per 1,000 requests.
   - SLO: 95.0% target over 2m window; achieved 97.35% (3 errors out of 113 requests).

---

## 2. Directory Structure

```text
.
├── cloud_assignment/       # Immutable assignment kit (data, tools, schema, rate_card)
├── prompts/
│   └── teacher_prompt.txt  # System prompt for Phi-3.5 4-key JSON generation
├── worker/
│   ├── clean.py            # Shard cleaning, validation, deduplication, S3 upload
│   ├── worker.py           # Sharded worker script for teacher dataset generation
│   └── Dockerfile          # Containerfile for worker jobs
├── training/
│   ├── config.yaml         # Training hyperparameters and environment versions
│   ├── train.py            # Causal LM training loop with loss logging
│   └── loss.csv            # Measured epoch loss history
├── service/
│   ├── app.py              # FastAPI microservice (/parse, /healthz, /readyz)
│   └── requirements.txt    # Pinned production dependencies
├── cluster/
│   └── k3d.yaml            # k3d cluster specification (port 8080:80)
├── storage/
│   └── seaweedfs.yaml      # SeaweedFS deployment in 'data' namespace
├── k8s/
│   ├── namespace.yaml      # Namespaces: data, pipeline, app
│   ├── secret.yaml         # Development S3 credentials
│   ├── deployment.yaml     # 2 replicas, probes, resource limits
│   ├── service.yaml        # ClusterIP service
│   ├── ingress.yaml        # Traefik Ingress routing /parse
│   └── hpa.yaml            # HorizontalPodAutoscaler (min 1, max 2, 70% CPU)
├── network/
│   ├── subnets.md          # Subnet allocation table, working, and technical rationale
│   └── nacl.json           # Stateless NACL rules for public subnet
├── tests/
│   ├── test_cleaning_rules.py  # Unit tests for data cleaning rules (a)-(e)
│   ├── test_service_schema.py  # Unit tests for FastAPI endpoints & validation
│   └── test_nacl_rules.py      # Unit tests for stateless NACL evaluation
├── .github/
│   └── workflows/
│       └── ci.yml          # CI/CD pipeline (lint, test, model eval, gitleaks)
├── results/                # Complete empirical logs, predictions, and benchmarks
├── report/
│   ├── generate_report.py  # ReportLab PDF report generator
│   └── report.pdf          # 3-page academic report
├── reflection/
│   └── 230101093.pdf       # 3-page student reflection document
├── Dockerfile              # Production CPU-only container image build
├── Makefile                # Lifecycle management targets
├── AI_USE.md               # AI transparency disclosure
├── COMPLETION_STATUS.md    # Requirement verification matrix
├── FINAL_AUDIT.md          # Post-execution compliance audit
└── README.md
```

---

## 3. Quickstart & Lifecycle Commands

### Prerequisites
- Python 3.11 with virtual environment (`.venv`)
- Docker Desktop (running Linux containers)
- `k3d` CLI and `kubectl` CLI

### Build and Deploy (`make up`)
```bash
make up
```
This single command:
1. Creates the k3d cluster from `cluster/k3d.yaml`.
2. Applies namespaces (`data`, `pipeline`, `app`) and secrets (`s3-credentials`).
3. Deploys SeaweedFS in namespace `data` and initializes `datasets` and `models` buckets.
4. Builds the container image `command-parser-service:latest` and imports it into k3d.
5. Deploys the service, ingress, and HPA in namespace `app`.
6. Waits for the deployment rollout to reach Ready state.

### Run Unit Tests (`make test`)
```bash
make test
```
Executes all 23 unit tests across cleaning rules, service schema validation, probes, and stateless NACL simulation.

### Run Code Linter (`make lint`)
```bash
make lint
```
Runs Flake8 across `worker`, `service`, `tests`, and `training` (0 errors).

### Verify Stateless NACL (`make nacl-check`)
```bash
make nacl-check
```
Runs `cloud_assignment/tools/nacl_sim.py` against `cloud_assignment/network/packets_sample.jsonl` (100% score).

### Train Student Model (`make train`)
```bash
make train SUBSET=50   # Quick test on first 50 records
make train             # Full training on first 1,500 records
```

### Tear Down (`make down`)
```bash
make down
```
Idempotently deletes all Kubernetes resources, manifests, and tears down the k3d cluster.
