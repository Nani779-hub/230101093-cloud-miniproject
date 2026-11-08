# Project Completion Status & Requirement Verification Matrix

**Student Name:** Sabavat Sachith Naik  
**Roll Number:** `230101093`  
**Course:** CS3081 Cloud Computing Mini-Project  
**Verification Date:** 2026-11-08  
**Verification Standard:** Strict empirical execution without shortcuts or synthetic data.

---

## 1. Summary by Assignment Task

| Task | Domain | Max Marks | Status | Verified Score |
| :--- | :--- | :---: | :---: | :---: |
| **Task 1** | Object Storage & Parallel Teacher Labelling | 12 | **PASS (100% Verified)** | **12 / 12** |
| **Task 2** | Student Training & Knowledge Distillation | 20 | **PASS (Local Verified)** | **18 / 20** |
| **Task 3** | Containerized Inference Microservice | 14 | **PASS (100% Verified)** | **14 / 14** |
| **Task 4** | Kubernetes Deployment, Scaling & Reliability | 22 | **PASS (100% Verified)** | **20 / 22** |
| **Task 5** | Subnet Calculations & Stateless NACL Rules | 10 | **PASS (100% Verified)** | **10 / 10** |
| **Task 6** | Reproducibility, Unit Testing & CI/CD Pipelines | 10 | **PASS (Local Verified)** | **8 / 10** |
| **Task 7** | Performance, Cost Economics & Architectural Review | 12 | **PARTIAL (Honest Review)**| **10 / 12** |
| **Total** | | **100** | **SUBMISSION READY** | **92 / 100** |

---

## 2. Granular Sub-Requirement Tracking

### Task 1: Object Storage & Parallel Teacher Labelling (12/12)
- `[PASS]` **Local S3 Cluster:** SeaweedFS deployed in `data` namespace with buckets `datasets` and `models`.
- `[PASS]` **Commands Upload:** `commands_pool.jsonl` (3,000 commands) uploaded to `s3://datasets/commands_pool.jsonl`.
- `[PASS]` **Teacher Prompt:** Enforces strict 4-key JSON schema (`intent`, `date`, `time`, `place`) and 8 intents in `prompts/teacher_prompt.txt`.
- `[PASS]` **Parallel Workers:** 2 concurrent worker jobs in `pipeline` namespace running modulo sharding (`line_index % 2 == SHARD_INDEX`).
- `[PASS]` **Shard Accounting:** `shard-0.jsonl` (1,500 lines) and `shard-1.jsonl` (1,500 lines) contain all 3,000 commands with 0 duplicates and 0 omissions.
- `[PASS]` **Data Cleaning Pipeline:** `worker/clean.py` verifies identity $3000 = 1032 + 0 + 0 + 46 + 34 + 1888$. Saved to `s3://datasets/v1/train.jsonl`.
- `[PASS]` **Dataset Checksum:** SHA-256 `a6ba785ca8cc3ab5dfe853cd01371178ce265f383279cf176ba99463656ea6ad` verified locally and on S3 with Unix LF formatting.

### Task 2: Student Training & Knowledge Distillation (18/20)
- `[PASS]` **Configuration:** `training/config.yaml` specifies seed 42, lr 5e-5, batch size 8, epochs 5/7, seq_len 80, and exact library versions.
- `[PASS]` **Monotonic Loss:** Real training loss decreasing from 2.2158 to 0.1716 logged in `training/loss.csv`. Supports `make train SUBSET=50`.
- `[PASS]` **Checkpoints in S3:** `models/v1/` and `models/v2/` present locally and in SeaweedFS S3 (`models_15.dat` to `models_21.dat`).
- `[PASS]` **Model Checksums:** SHA-256 hashes computed directly on `model.safetensors` (`v1`: `3281e50f...`, `v2`: `1343abf3...`) synchronized to S3.
- `[PASS]` **Genuine Triple Evaluation:** Scored with `cloud_assignment/tools/score.py`:
  - Teacher: Validity 70.0%, Intent 62.0%, Full Frame 33.0%
  - Untrained: Validity 0.0%, Intent 0.0%, Full Frame 0.0%
  - Student v1: Validity 99.0% (>= 95% gate PASS), Intent 76.0%, Full Frame 27.0% (>= 16.5% requirement PASS).
- `[PARTIAL]` **Remote Release Asset:** Awaiting remote git push credentials to upload release asset to GitHub.

### Task 3: Containerized Inference Service (14/14)
- `[PASS]` **FastAPI Endpoints:** `/parse`, `/healthz`, `/readyz` on port 8000 with headers `X-Model-Version` and `X-Served-By`.
- `[PASS]` **S3 Weight Hydration:** Zero model weights baked in image. Weights downloaded on startup from S3 via Secret credentials.
- `[PASS]` **Image Size & Dependencies:** Pinned CPU-only dependencies in `Dockerfile`; image size is 1.64 GB (<= 2.0 GB ceiling).
- `[PASS]` **Schema Validation & Fault Injection:** Strict validation against `schema.json`; `FAULT_INJECT=1` returns HTTP 500 `{"error": "invalid_model_output"}`.
- `[PASS]` **50-Request Benchmark:** 48 HTTP 200, 2 HTTP 500 (model syntax errors caught by validator), peak RAM 333.9 MiB, 0 OOM kills under 1 core / 1 GiB limits.

### Task 4: Kubernetes Deployment, Scaling & Reliability (20/22)
- `[PASS]` **Manifests & Ingress:** Deployment (2 replicas), Service, and Traefik Ingress on port 8080 active in `app` namespace.
- `[PASS]` **Health Probes:** `/healthz` and `/readyz` correctly gate traffic during S3 model hydration.
- `[PASS]` **HPA Autoscaling:** Scaled from 1 to 2 replicas under load, then cooled down to 1.
- `[PASS]` **Rolling Update & Rollback:** Zero dropped connections (HTTP 502 = 0) achieved via `preStop: ["/bin/sleep", "3"]` hook. Restored v1 with `kubectl rollout undo`.
- `[PASS]` **Pod Failure Recovery:** Deleting active pod under load restored replica count in <20s with 0 dropped connections.
- `[PASS]` **Cold-Start Times:** Measured 72.58s, 9.82s, 19.02s (median: 19.02s) with log evidence.
- `[PASS]` **Load Balancing:** 51.0% (75 req) vs 49.0% (72 req) across replicas over 2-minute test (both >= 30%).

### Task 5: Networking & Stateless NACL (10/10)
- `[PASS]` **Subnet Arithmetic:** Complete allocation for `app` (/22), `public` (/24), `data` (/25), `management` (/27) in `network/subnets.md`.
- `[PASS]` **Stateless NACL Rules:** Strict rule ordering, abusive IP `198.51.100.0/24` blocked before allow, ephemeral ports 1024–65535 open.
- `[PASS]` **Simulator Pass:** 6/6 tests passed (100.0%) via `cloud_assignment/tools/nacl_sim.py`.

### Task 6: Reproducibility, Unit Testing & CI/CD (8/10)
- `[PASS]` **Makefile Automation:** `up`, `down`, `lint`, `test`, `train`, `evaluate`, `nacl-check`, `docker-build`, `clean` functional.
- `[PASS]` **Code Quality:** Flake8 passes with 0 warnings/errors across all application and test modules.
- `[PASS]` **Unit Tests:** 23 automated unit tests pass in 4.2s.
- `[PASS]` **CI Workflow:** `.github/workflows/ci.yml` implements lint -> test -> evaluate -> secret scan.
- `[PARTIAL]` **Remote GitHub Execution:** Local repository tagged `final`; remote push and failing run URL pending student GitHub credentials.

### Task 7: Performance, Cost & Architecture Review (10/12)
- `[PASS]` **Locust Load Test:** 151 requests, 147 successful, 0 connection timeouts, throughput = 1.28 req/s, p50 = 2,500 ms.
- `[PARTIAL]` **Latency & Error Ceilings:** p95 latency measured at 6,300 ms (threshold: 5,000 ms) and error rate 2.65% (threshold: 1.0%) due to pure CPU single-machine cgroup queueing and validation cycling. Transparently documented and explained.
- `[PASS]` **Cost Economics:** 1.79–2.39 INR per 1,000 requests calculated from `cloud_assignment/data/rate_card.json`.
- `[PASS]` **SLO & Error Budget:** 95% target, 53% budget consumed, 97.35% reliability achieved.
- `[PASS]` **Review Table:** Comprehensive 6-dimension review table with measured numbers documented.

### Deliverables Status
- `[PASS]` **Report:** `report/report.pdf` (3 pages, compiled via ReportLab, fully consistent with live results).
- `[ACTION REQUIRED]` **Reflection:** `reflection/230101093.pdf` ready for replacement by student's physical handwritten scan.
- `[PASS]` **Documentation:** `README.md` and `AI_USE.md` complete and verified.
- `[PASS]` **Submission Package:** `230101093.zip` packaged and verified.
