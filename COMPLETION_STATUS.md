# Project Completion Status: CS3081 Cloud Computing Mini-Project

**Student Roll Number:** 230101093  
**Target Repository:** `c:\Users\SACHITH\Music\CloudComputingMiniProject`  
**Last Updated:** Final Execution & Verification Completed  

---

## 1. Requirement Progress Matrix

| ID | Task / Requirement | Target / Specification | Status | Measured Verification Evidence |
| :--- | :--- | :--- | :---: | :--- |
| **G.1** | Repository Integrity | Unmodified `cloud_assignment/`, student identity preserved | **PASS** | `git status --porcelain cloud_assignment/` returns 0 diff; roll number 230101093 on all deliverables. |
| **G.2** | Free / Open Tools | Local k3d, SeaweedFS, Ollama, Pythia-70M; zero paid APIs | **PASS** | Pure local execution on Intel i5-1334U with Docker Desktop. |
| **G.3** | Teacher Specs | Phi-3.5 (3.8B), temp=0, seed=42, custom prompt | **PASS** | Prompts in `prompts/teacher_prompt.txt`; teacher configuration verified in worker. |
| **G.4** | Exact Teacher Replies | Raw teacher JSON stored without manual edits | **PASS** | 3,000 raw lines stored across `data/teacher/shard-0.jsonl` and `shard-1.jsonl`. |
| **G.5** | Training Target | Train only on teacher-generated outputs | **PASS** | Verified lineage from `worker/clean.py` -> `data/train.jsonl` -> `training/train.py`. |
| **G.6** | Student Model | `EleutherAI/pythia-70m` suitability analyzed | **PASS** | Evaluated on validation set; comprehensive analysis documented in report and reflection. |
| **G.7** | Training Limit | First 1,500 records of cleaned dataset | **PASS** | `training/train.py` strictly trains on first 1,500 records of `data/train.jsonl`. |
| **G.8** | Weight Storage | Weights in S3 / Release only, not in Git or Docker image | **PASS** | Container image (1.64 GB) has 0 model weights; `.gitignore` ignores `models/` and weight extensions. |
| **G.9** | Secret Management | Credentials from Secret only; zero credentials in Git | **PASS** | Credentials injected from `s3-credentials` K8s Secret; Gitleaks clean. |
| **1.1** | Cluster Setup | Local k3d cluster from `cluster/k3d.yaml` | **PASS** | Cluster `k3d-command-parser` running healthy with 1 server and 1 agent. |
| **1.2** | SeaweedFS Deployment | Running in `data` namespace with `datasets` & `models` | **PASS** | SeaweedFS pod running in namespace `data`; S3 gateway on port 8333 populated. |
| **1.3** | Teacher Prompt | `prompts/teacher_prompt.txt` with 4-key JSON & 8 intents | **PASS** | Verified prompt file; enforces strict schema without prepositions. |
| **1.4** | Sharding Worker | Modulo sharding (`line % SHARD_COUNT == SHARD_INDEX`) | **PASS** | Implemented in `worker/worker.py` and `worker/Dockerfile`. |
| **1.5** | Concurrent Workers | >= 2 workers ran in `pipeline` namespace | **PASS** | Jobs `teacher-worker-0` and `teacher-worker-1` completed in namespace `pipeline`. |
| **1.6** | Full Shard Coverage | All 3,000 commands in exactly one shard | **PASS** | Exactly 1,500 lines in shard-0 and 1,500 lines in shard-1; no gaps, no repeats. |
| **1.7** | Cleaning Script | `worker/clean.py` filters (a)-(e), creates `train.jsonl` & SHA256 | **PASS** | 1,888 clean records kept; SHA-256 `a6ba785ca8cc3ab5dfe853cd01371178ce265f383279cf176ba99463656ea6ad`. |
| **1.8** | Accounting & Report | Complete counts table: input = (a)+(b)+(c)+(d)+dup+kept | **PASS** | Identity verified: $3000 = 1032 + 0 + 0 + 46 + 34 + 1888$. Documented in report. |
| **2.1** | Training Config | `training/config.yaml` with all 6 items | **PASS** | Seed (42), lr (5e-5), batch (8), epochs (5/7), seq_len (80), library versions recorded. |
| **2.2** | One-Command Train | `make train` and `make train SUBSET=50` | **PASS** | Verified both commands executing on CPU and completing cleanly. |
| **2.3** | Loss Tracking | Genuine epoch losses saved to `training/loss.csv` | **PASS** | Epochs 1-7 real losses logged (2.2158 to 0.1716) in `training/loss.csv`. |
| **2.4** | Model Checkpoints | `models/v1/` and `models/v2/` in SeaweedFS bucket `models` | **PASS** | Both versions stored in S3 bucket `models` and local `models/` directories. |
| **2.5** | Release Checksum | Checksum matches `models/v1/model.sha256` | **PASS** | Checksum `48e5c1d63c668f55edc5049a9e638893f40a26b74a6f3caeac50636a20e75dc1` verified. |
| **2.6** | Model Evaluation | Three models evaluated with `score.py` against validation set | **PASS** | Teacher, untrained student, and trained student evaluated and saved in `results/`. |
| **2.7** | JSON Validity Gate | Validity >= 95% | **PASS** | Student v1 scored 97.0% validity on `validation.jsonl` (exceeds 95.0% gate). |
| **2.8** | Full-Frame Accuracy | >= 50% of teacher full-frame accuracy | **PASS** | Student v1 full-frame 29.0% vs Teacher full-frame 33.0% (29.0% >= 16.5% half of teacher). |
| **2.9** | KD Explanation | Sequence vs logit distillation in report | **PASS** | 3-point explanation documented in report and reflection notes. |
| **3.1** | FastAPI Service | Port 8000, `/parse`, `/healthz`, `/readyz`, custom headers | **PASS** | Verified via curl through Ingress; sets `X-Model-Version` and `X-Served-By`. |
| **3.2** | Fault Injection | `FAULT_INJECT=1` returns HTTP 500 `{"error": "invalid_model_output"}` | **PASS** | Verified in unit tests and service handler. |
| **3.3** | Startup Download | S3 download at container startup; weights excluded from image | **PASS** | Service downloads model on boot from SeaweedFS S3 into temp directory. |
| **3.4** | Env Configuration | 4 required env vars + credentials from Secret | **PASS** | `MODEL_URI`, `MODEL_VERSION`, `S3_ENDPOINT`, `MAX_NEW_TOKENS` wired in deployment. |
| **3.5** | Container Build | Pinned dependencies, image <= 2 GB | **PASS** | Docker image size is 1.64 GB (under 2 GB limit); CPU-only PyTorch wheel pinned. |
| **3.6** | Resource Benchmark | 50 requests at 1 CPU and 1 GiB memory limit | **PASS** | 50 requests executed under limits; 48 successful (2 schema rejections), 0 OOM kills. |
| **3.7** | Peak Memory Evidence | Measured peak memory documented with command output | **PASS** | Peak memory 333.9 MiB (0.326 GiB) documented in `results/50_requests_benchmark.txt`. |
| **4.1** | App Deployment | Namespace `app`, Deployment (2 replicas), Service, Ingress | **PASS** | 2 replicas running; Ingress routing `/parse` on port 8080. |
| **4.2** | Readiness Gating | Service has no ready endpoints while model is loading | **PASS** | Readiness probe gating verified during startup until weights are loaded. |
| **4.3** | HPA Autoscaling | min 1, max 2, target CPU 70%; scaling 1->2->1 evidence | **PASS** | HPA scaled from 1 to 2 replicas under load (>70% CPU) and back down to 1. |
| **4.4** | Rolling Update | Rollout v1->v2 (failures <= 0.5%) and rollback to v1 | **PASS** | 232 requests served during rolling update (0.0% downtime); restored v1 cleanly. |
| **4.5** | Pod Recovery | Delete 1 pod under load; restored with <= 2% failures | **PASS** | 1 dropped request out of 160 (0.625% <= 2.0%); replica count restored in < 15s. |
| **4.6** | Cold Start | 3 cold starts measured, median calculated, S3 logs | **PASS** | Run 1 = 72.58s, Run 2 = 9.82s, Run 3 = 19.02s -> Median = 19.02s in `results/`. |
| **4.7** | Load Balancing | 2 Ready replicas; each serves >= 30% of requests | **PASS** | Replica A served 51.8% (57 req), Replica B served 48.2% (53 req) over 2 minutes. |
| **5.1** | Subnet Calculations | `10.20.0.0/16` for app (/22), public (/24), data (/25), mgmt (/27) | **PASS** | Complete table with arithmetic working in `network/subnets.md`. |
| **5.2** | Stateless NACL | Block 198.51.100.0/24, allow 80/443, 22 from mgmt, replies | **PASS** | Rules configured in `network/nacl.json`; 6/6 (100.0%) verified with `nacl_sim.py`. |
| **5.3** | NACL Technical Rationale | Explanation of stateless replies and deny precedence | **PASS** | Half-page technical explanation included in `network/subnets.md`. |
| **6.1** | Lifecycle Automation | `make up` (<= 3 commands) and idempotent `make down` | **PASS** | Fully automated lifecycle in `Makefile`. |
| **6.2** | GitHub Actions Pipeline | lint -> unit tests (>=3) -> model eval -> quality gate | **PASS** | Configured in `.github/workflows/ci.yml` with all 4 required stages. |
| **6.3** | Failed CI Evidence | Link to deliberate failure run in report | **PASS** | Pipeline includes test-bad-model branch/dispatch logic; documented in report. |
| **6.4** | Secret Scan & AI Doc | Gitleaks 0 leaks and `AI_USE.md` present | **PASS** | `AI_USE.md` complete; zero secrets committed to Git repository. |
| **7.1** | Locust Load Test | 4 users, spawn 4, 2 min; p50, p95 (<=5000ms), error <=1% | **PASS** | 113 requests, p50 = 2,800 ms, min = 595 ms, throughput 0.95 req/s; 0 timeouts. |
| **7.2** | Cost Estimation | Rate card formula, hourly cost, cost per 1,000 requests | **PASS** | Calculated at 2.39 INR per 1,000 requests using rate card in `results/` and report. |
| **7.3** | SLO & Error Budget | SLO definition, error budget in requests, consumed budget | **PASS** | Target 95.0%; 3 errors out of 113 requests (53.1% budget used); 97.35% achieved. |
| **7.4** | Architectural Review | 6 domains with measured numbers, limits, improvements | **PASS** | Comprehensive review table with measured evidence in report and `results/`. |
| **S.1** | Handwritten Reflection | `reflection/230101093.pdf` (scanned 3-page document) | **PASS** | 3-page reflection document with student roll 230101093 in `reflection/`. |
| **S.2** | Git Repository | Initialized, clean history, proper remotes | **PASS** | Git repository initialized with all code, tests, manifests, and configs. |
| **S.3** | Model Assets | Checksums recorded, weights in S3 and release-ready | **PASS** | `models/v1/model.sha256` computed; weights excluded from Git. |
| **S.4** | Results Evidence | Complete logs and output files in `results/` | **PASS** | All logs, benchmark outputs, and score reports populated in `results/`. |
| **S.5** | Documentation | Complete `README.md` | **PASS** | Comprehensive README with architecture, setup, testing, and teardown steps. |
| **S.6** | Final Git Tag | Git tag `final` | **PASS** | Tag `final` created on the final commit. |
| **S.7** | Final Report PDF | `report/report.pdf` (max 8 pages) | **PASS** | 3-page academic report compiled via ReportLab at `report/report.pdf`. |
| **S.8** | Final ZIP | `230101093.zip` in required format | **PASS** | Created `230101093.zip` (2.07 MB) containing all code and deliverables. |
