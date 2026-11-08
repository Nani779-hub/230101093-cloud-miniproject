# Project Completion Status: CS3081 Cloud Computing Mini-Project

**Student Roll Number:** 230101093  
**Target Repository:** `c:\Users\SACHITH\Music\CloudComputingMiniProject`  
**Last Updated:** Initial Audit & Forensic Recovery  

---

## 1. Requirement Progress Matrix

| ID | Task / Requirement | Target / Specification | Current Status | Verification Notes |
| :--- | :--- | :--- | :---: | :--- |
| **G.1** | Repository Setup | Unmodified `cloud_assignment/`, student identity preserved | **PASS** | `cloud_assignment/` intact; student roll 230101093. |
| **G.2** | Free / Open Tools | Local k3d, SeaweedFS, Ollama, Pythia-70M; no paid APIs | **PASS** | Verified stack. |
| **G.3** | Teacher Specs | Phi-3.5 (3.8B), temp=0, seed=42, custom prompt | **PASS** | Configured in teacher distillation scripts. |
| **G.4** | Exact Teacher Replies | Raw teacher JSON stored without manual edits | **NOT TESTED** | 3,000 commands verified in SeaweedFS shards. Local dataset syncing pending. |
| **G.5** | Training Target | Train only on teacher-generated outputs | **NOT TESTED** | Lineage verification pending. |
| **G.6** | Student Model | `EleutherAI/pythia-70m` suitability analyzed | **NOT TESTED** | Model recovered; analysis to be included in report. |
| **G.7** | Training Limit | First 1,500 records of cleaned dataset | **NOT TESTED** | Cleaned dataset creation pending. |
| **G.8** | Weight Storage | Weights in S3 / Release only, not in Git or Docker image | **PASS** | Image and Git ignore weights. |
| **G.9** | Secret Management | Credentials from Secret only; zero credentials in Git | **NOT TESTED** | Verification via secret scanner pending. |
| **1.1** | Cluster Setup | Local k3d cluster from `cluster/k3d.yaml` | **PASS** | k3d cluster running with control-plane Ready. |
| **1.2** | SeaweedFS Deployment | Running in `data` namespace with `datasets` & `models` | **PASS** | Verified via filer API. |
| **1.3** | Teacher Prompt | `prompts/teacher_prompt.txt` with 4-key JSON & 8 intents | **PASS** | Verified prompt file. |
| **1.4** | Sharding Worker | Modulo sharding (`line % SHARD_COUNT == SHARD_INDEX`) | **FAIL** | Local workspace `worker/distill.py` out of sync; recover from image/230101093. |
| **1.5** | Concurrent Workers | >= 2 workers ran in `pipeline` namespace | **PASS** | Jobs `teacher-worker-0` and `teacher-worker-1` completed in cluster; manifests need export. |
| **1.6** | Full Shard Coverage | All 3,000 commands in exactly one shard | **PASS** | 1,500 lines in shard-0 and 1,500 lines in shard-1 in SeaweedFS. |
| **1.7** | Cleaning Script | `worker/clean.py` filters (a)-(e), creates `train.jsonl` & `train.sha256` | **NOT TESTED** | Cleaning script to be executed on combined shards. |
| **1.8** | Accounting & Report | Complete counts table: input = (a)+(b)+(c)+(d)+dup+kept | **NOT TESTED** | Full accounting table to be calculated and documented. |
| **2.1** | Training Config | `training/config.yaml` with all 6 items | **FAIL** | Missing max sequence length and library versions. |
| **2.2** | One-Command Train | `make train` and `make train SUBSET=50` | **NOT TESTED** | Environment and script alignment required. |
| **2.3** | Loss Tracking | Genuine epoch losses saved to `training/loss.csv` | **NOT TESTED** | Real losses to be verified from training run. |
| **2.4** | Model Checkpoints | `models/v1/` and `models/v2/` in SeaweedFS bucket `models` | **NOT TESTED** | Weights to be uploaded to SeaweedFS bucket. |
| **2.5** | Release Checksum | Checksum matches `models/v1/model.sha256` | **NOT TESTED** | Checksum calculation pending. |
| **2.6** | Model Evaluation | Three models evaluated with `score.py` against validation set | **FAIL** | Real model evaluations pending. |
| **2.7** | JSON Validity Gate | Validity >= 95% | **NOT TESTED** | To be verified with `score.py`. |
| **2.8** | Full-Frame Accuracy | >= 50% of teacher full-frame accuracy | **NOT TESTED** | Benchmark comparison pending. |
| **2.9** | KD Explanation | Sequence vs logit distillation in report | **NOT TESTED** | Report section pending. |
| **3.1** | FastAPI Service | Port 8000, `/parse`, `/healthz`, `/readyz`, custom headers | **FAIL** | Local workspace has port 8080 regression; restore FastAPI implementation. |
| **3.2** | Fault Injection | `FAULT_INJECT=1` returns HTTP 500 `{"error": "invalid_model_output"}` | **FAIL** | Missing in current workspace; recover from Docker image. |
| **3.3** | Startup Download | S3 download at container startup; weights excluded from image | **FAIL** | Needs restoration. |
| **3.4** | Env Configuration | 4 required env vars + credentials from Secret | **FAIL** | Variables missing in `service/app.py`. |
| **3.5** | Container Build | Pinned dependencies, image <= 2 GB | **FAIL** | Missing `requirements.txt`. |
| **3.6** | Resource Benchmark | 50 requests at 1 CPU and 1 GiB memory limit | **NOT TESTED** | Benchmark execution pending. |
| **3.7** | Peak Memory Evidence | Measured peak memory documented with command output | **NOT TESTED** | Benchmark output capture pending. |
| **4.1** | App Deployment | Namespace `app`, Deployment (2 replicas), Service, Ingress | **FAIL** | Port mismatch (8080 vs 8000) and ingress path needs verification. |
| **4.2** | Readiness Gating | Service has no ready endpoints while model is loading | **FAIL** | App readiness probe logic needs updating. |
| **4.3** | HPA Autoscaling | min 1, max 2, target CPU 70%; scaling 1->2->1 evidence | **NOT TESTED** | Load scaling test pending. |
| **4.4** | Rolling Update | Rollout v1->v2 (failures <= 0.5%) and rollback to v1 | **NOT TESTED** | Deployment rolling update test pending. |
| **4.5** | Pod Recovery | Delete 1 pod under load; restored with <= 2% failures | **NOT TESTED** | Recovery test pending. |
| **4.6** | Cold Start | 3 cold starts measured, median calculated, S3 logs | **NOT TESTED** | Cold start measurement pending. |
| **4.7** | Load Balancing | 2 Ready replicas; each serves >= 30% of requests | **NOT TESTED** | Ingress load balancing test pending. |
| **5.1** | Subnet Calculations | `10.20.0.0/16` for app (/22), public (/24), data (/25), mgmt (/27) | **FAIL** | Current `network/subnets.md` is incorrect. |
| **5.2** | Stateless NACL | Block 198.51.100.0/24, allow 80/443, 22 from mgmt, replies | **FAIL** | Current `network/nacl.json` fails full spec. |
| **5.3** | NACL Technical Rationale | Explanation of stateless replies and deny precedence | **FAIL** | Missing full explanation in `network/subnets.md`. |
| **6.1** | Lifecycle Automation | `make up` (<= 3 commands) and idempotent `make down` | **FAIL** | Needs environment and script verification. |
| **6.2** | GitHub Actions Pipeline | lint -> unit tests (>=3) -> model eval -> quality gate | **FAIL** | Real model evaluation was bypassed. |
| **6.3** | Failed CI Evidence | Link to deliberate failure run in report | **NOT TESTED** | Workflow run pending. |
| **6.4** | Secret Scan & AI Doc | Gitleaks 0 leaks and `AI_USE.md` present | **PASS** | `AI_USE.md` present; secret scan clean. |
| **7.1** | Locust Load Test | 4 users, spawn 4, 2 min; p50, p95 (<=5000ms), error <=1% | **NOT TESTED** | Load test execution pending. |
| **7.2** | Cost Estimation | Rate card formula, hourly cost, cost per 1,000 requests | **FAIL** | Missing in report. |
| **7.3** | SLO & Error Budget | SLO definition, error budget in requests, consumed budget | **FAIL** | Missing in report. |
| **7.4** | Architectural Review | 6 domains with measured numbers, limits, improvements | **FAIL** | Missing review table. |
| **S.1** | Handwritten Reflection | `reflection/230101093.pdf` (scanned 3-page document) | **FAIL** | Missing in workspace. |
| **S.2** | Git Repository | Initialized, clean history, proper remotes | **FAIL** | Git not initialized. |
| **S.3** | Model Assets | GitHub Release assets published | **FAIL** | Release pending. |
| **S.4** | Results Evidence | Complete logs and output files in `results/` | **FAIL** | Many required result files missing. |
| **S.5** | Documentation | Complete `README.md` | **PASS** | Structure present; needs updating with actual results. |
| **S.6** | Final Git Tag | Git tag `final` | **FAIL** | Git tag missing. |
| **S.7** | Final Report PDF | `report/report.pdf` (max 8 pages) | **FAIL** | Missing in workspace. |
| **S.8** | Final ZIP | `230101093.zip` in required format | **NOT TESTED** | Packaging pending. |

