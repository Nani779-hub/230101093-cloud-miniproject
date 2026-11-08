# Final Assignment-Compliance Audit Report

**Project Title:** Knowledge Distillation and Deployment of a Lightweight Command-Parsing Language Model on a Local Cloud  
**Course Code:** Cloud Computing (CS3081)  
**Student Roll Number:** 230101093  
**Audit Date:** 2026-11-08  
**Audit Target:** `c:\Users\SACHITH\Music\CloudComputingMiniProject`  
**Reference Handout:** `CLOUD_ASSIGNMENT_DESCRIPTION.pdf` & `cloud_assignment/README.md`  

---

## Executive Summary

This compliance audit evaluates every requirement specified in the Cloud Computing Mini Project handout (`CLOUD_ASSIGNMENT_DESCRIPTION.pdf`) and student kit against the current codebase in `CloudComputingMiniProject`.

The project was inspected across source code, Kubernetes manifests, CI/CD workflows, training scripts, evaluation scripts, cluster state, and test results. Each requirement is assigned a strict status:
- **`PASS`**: Requirement is fully implemented in code, executed, and backed by verifiable measured evidence.
- **`FAIL`**: Code or configuration is missing, non-compliant, hardcoded, or produces incorrect results.
- **`NOT TESTED`**: Code exists but has not been executed, or cannot be tested due to missing dependencies, cluster components, or data artifacts.

### Overall Compliance Scorecard

| Task | Topic | Max Marks | Current Status | Estimated Marks |
| :--- | :--- | :---: | :---: | :---: |
| **Task 1** | Object Storage & Parallel Teacher Labelling | 12 | **PARTIAL** | 4 / 12 |
| **Task 2** | Student Training (Sequence-Level Distillation) | 20 | **FAIL** | 2 / 20 |
| **Task 3** | Inference Service in a Container | 14 | **FAIL** | 2 / 14 |
| **Task 4** | Kubernetes Deployment, Scaling & Reliability | 22 | **NOT TESTED** | 0 / 22 |
| **Task 5** | Subnetting & Network Access Control (NACL) | 10 | **FAIL** | 1 / 10 |
| **Task 6** | Reproducibility, Testing, and CI/CD | 10 | **FAIL** | 2 / 10 |
| **Task 7** | Performance, Cost, SLO & Architectural Review | 12 | **FAIL** | 0 / 12 |
| **Deliverables** | Final Report, Reflection PDF, Tag, Git State | — | **FAIL** | — |
| **TOTAL** | **Full Assignment Scope** | **100** | **NON-COMPLIANT** | **11 / 100** |

---

## 1. Requirement-by-Requirement Compliance Matrix

### General Project Requirements (Handout Section 6)

| # | Requirement | Implementing File & Function | Verification Command & Actual Result | Status | Missing Evidence & Incomplete Tasks |
| :- | :--- | :--- | :--- | :---: | :--- |
| **G.1** | Individual project using student kit | Root workspace | Verified `cloud_assignment/` exists and is unmodified. | **PASS** | None. |
| **G.2** | Open-source software and free tools only (no paid cloud, no paid inference API) | `worker/distill.py`, `cluster/k3d.yaml` | Inspected code; Ollama and local k3d specified. | **PASS** | None. |
| **G.3** | Fixed teacher model `phi3.5:latest` (3.8B), Ollama, `temperature=0`, `seed=42`, custom prompt | `worker/distill.py:query_ollama()`<br>`prompts/teacher_prompt.txt` | Inspected payload in `worker/distill.py` and `prompts/teacher_prompt.txt`. | **PASS** | None. |
| **G.4** | Store teacher replies exactly as generated without manual edits | `worker/distill.py:146-155` | Inspected `data/teacher_shards/shard-0.jsonl`. | **PASS** | Full 3,000 dataset only partially run in workspace (only 2 records on disk; 3,000 in cluster SeaweedFS from 2 days ago). |
| **G.5** | Train only on teacher-generated replies; no manual labels, other models, or validation data | `training/train.py:load_dataset()` | `training/config.yaml` points to `data/train.jsonl`. | **PASS** | Dataset file `data/train.jsonl` does not exist on disk. |
| **G.6** | Student model `EleutherAI/pythia-70m` | `training/config.yaml:9` | Inspected `config.yaml`. | **PASS** | Suitability assessment in report is missing. |
| **G.7** | Max 1,500 training examples: first 1,500 records in cleaned dataset | `training/train.py:137`<br>`training/config.yaml:11` | Inspected `train.py`. | **PASS** | Full training has not been executed in current workspace. |
| **G.8** | Store model weights in object storage; do not commit to Git or include in container image | `.gitignore:17-21`<br>`Dockerfile:11-15` | Inspected `.gitignore` and `Dockerfile`. | **PASS** | Neither `models/v1/` nor `models/v2/` exists in object storage or local disk. |
| **G.9** | Do not store credentials, keys, or passwords in Git | `k8s/secret.yaml:1-35` | Inspected `k8s/secret.yaml`; uses dummy dev strings. | **PASS** | Production secret mechanism documentation required. |

---

### Task 1: Object Storage and Parallel Teacher Labelling (12 Marks)

| # | Requirement | Implementing File & Function | Verification Command & Actual Result | Status | Missing Evidence & Incomplete Tasks |
| :- | :--- | :--- | :--- | :---: | :--- |
| **1.1** | Local K8s cluster created with k3d from `cluster/k3d.yaml` (2 marks) | `cluster/k3d.yaml`<br>`Makefile:38-39` | `kubectl get nodes`<br>`k3d` not in host PATH; k3d cluster was created 2 days ago (`rancher/k3s:v1.31.5-k3s1` container running). | **PASS** | Document k3d installation on Windows host. |
| **1.2** | SeaweedFS running in `data` namespace with buckets `datasets` and `models`, `commands_pool.jsonl` uploaded (2 marks) | `storage/seaweedfs.yaml`<br>`Makefile:43-51` | `kubectl exec -n data deploy/seaweedfs -- wget -q -O - http://127.0.0.1:8888/buckets/`<br>SeaweedFS is Running. Buckets `datasets` and `models` exist. `commands_pool.jsonl` (198 KB) is present in `datasets`. | **PASS** | None. |
| **1.3** | Teacher prompt in `prompts/teacher_prompt.txt` asking for 4-key JSON (intent, date, time, place) | `prompts/teacher_prompt.txt` | File inspected. Contains the 4 keys and 8 intents. | **PASS** | None. |
| **1.4** | Worker in `worker/` reading `SHARD_INDEX` and `SHARD_COUNT` env vars, taking `line % SHARD_COUNT == SHARD_INDEX`, writing `{"id": "...", "text": "...", "teacher_raw": "..."}` to own object (2 marks) | Current: `worker/distill.py`<br>Cluster image: `command-parser-worker:latest` (`worker.py`) | **Current workspace `worker/distill.py` does NOT read env vars or do modulo sharding** (uses sequential limit and `raw_response`).<br>**Cluster image `command-parser-worker:latest` DID implement it**. | **FAIL** (workspace)<br>*(Passed in cluster 2 days ago)* | Workspace `worker/distill.py` is out of sync with Docker image `command-parser-worker:latest` that actually ran. |
| **1.5** | Run at least 2 workers concurrently in `pipeline` namespace, each with different `SHARD_INDEX` (2 marks) | `k8s/` (missing worker manifests) | `kubectl get job,pod -n pipeline`<br>`teacher-worker-0` and `teacher-worker-1` both Completed 2d1h ago. Duration: 3h37m. | **PASS** (cluster evidence) | Kubernetes Job manifests for `teacher-worker-0` and `1` are missing from the repository `k8s/` folder. |
| **1.6** | Every command ID appears in exactly one shard output: no gaps, no repeats (2 marks) | SeaweedFS: `datasets/teacher/shard-0.jsonl` & `shard-1.jsonl` | `kubectl exec -n data deploy/seaweedfs -- sh -c "wget -q -O - http://127.0.0.1:8888/buckets/datasets/teacher/shard-0.jsonl \| wc -l; wget -q -O - http://127.0.0.1:8888/buckets/datasets/teacher/shard-1.jsonl \| wc -l"`<br>Result: 1,500 and 1,500 lines. Total = 3,000. | **PASS** (in SeaweedFS) | Local directory `data/teacher_shards/` has only `shard-0.jsonl` with 2 lines. Shards must be downloaded to workspace. |
| **1.7** | `worker/clean.py` reads shard outputs, removes bad records ((a) invalid JSON, (b) wrong keys, (c) invalid intent, (d) invalid slot, (e) duplicates keeping smallest ID), writes to `datasets/v1/train.jsonl` and `train.sha256` in ID order (2 marks) | `worker/clean.py:clean_dataset()` | `worker/clean.py` takes a single file argument, writes to `data/train.jsonl` by default rather than reading all shards and writing to `datasets/v1/train.jsonl`. Neither `data/train.jsonl` nor `datasets/v1/train.jsonl` exists in the workspace or S3. | **FAIL** | Shard outputs were never cleaned to create `datasets/v1/train.jsonl` and `train.sha256`. |
| **1.8** | Report contains complete counts table: input = (a) + (b) + (c) + (d) + duplicates + kept, and half-page sharding explanation (2 marks) | `report/report.pdf` | `report/report.pdf` does NOT exist. | **FAIL** | Missing report and cleaning run accounting table over all 3,000 records. |

---

### Task 2: Training the Student (Sequence-Level Distillation) (20 Marks)

| # | Requirement | Implementing File & Function | Verification Command & Actual Result | Status | Missing Evidence & Incomplete Tasks |
| :- | :--- | :--- | :--- | :---: | :--- |
| **2.1** | `training/config.yaml` records all 6 items: random seed, learning rate, batch size, number of epochs, maximum sequence length, library versions (2 marks) | `training/config.yaml` | `Get-Content training/config.yaml`<br>Contains: seed, lr, batch_size, num_epochs.<br>**MISSING:** `maximum sequence length` and `library versions`. | **FAIL** | `max_seq_length` and library versions (`torch`, `transformers`) are absent from `config.yaml`. |
| **2.2** | Training runs with `make train`, reading only `config.yaml`. Supports `make train SUBSET=50`. (2 marks) | `Makefile:78-80`<br>`training/train.py:main()` | `.venv\Scripts\python.exe training/train.py --subset 50`<br>`train.py` falls back to printing an environment notice because `torch` and `transformers` are not installed in `.venv`. `data/train.jsonl` is missing. | **FAIL** | PyTorch/Transformers not installed in `.venv`; `data/train.jsonl` does not exist; actual fine-tuning loop cannot run. |
| **2.3** | Loss saved for every epoch in `training/loss.csv`; seed fixed in code (2 marks) | `training/train.py:record_loss()`<br>`training/loss.csv` | `training/loss.csv` exists with 3 lines, but generated via mock placeholder in `train.py:252` when imports fail. | **FAIL** | Loss values (`2.4512, 1.8340, 1.2105`) are hardcoded synthetic fallbacks, not measured training losses. |
| **2.4** | Save model and tokenizer to bucket `models` under `models/v1/` and `models/v2/` (2 marks) | `training/train.py:train()` | `kubectl exec -n data deploy/seaweedfs -- wget -q -O - http://127.0.0.1:8888/buckets/models/`<br>Result: `{"Entries": null, "EmptyFolder": true}`. Neither `v1` nor `v2` exists in S3 or local `models/`. | **FAIL** | No trained student model weights exist in object storage or `models/`. |
| **2.5** | Checksum of GitHub Release asset matches `models/v1/model.sha256` (2 marks) | Remote GitHub Release | `git status` -> `fatal: not a git repository`. No GitHub Release exists. No `models/v1/model.sha256` exists. | **FAIL** | Git is not initialized; no GitHub repo; no release assets published. |
| **2.6** | Run `score.py` on `validation.jsonl` for three models: teacher, untrained Pythia-70M, trained student. Raw outputs and score reports in `results/`, side-by-side in report. Teacher score saved as `results/teacher_validation.json` (2 marks) | `evaluation/evaluate.py`<br>`results/` | `results/predictions.jsonl` exists but was generated using regex `service.parser.CommandParser`!<br>`results/untrained_student_predictions.jsonl` has fake string `"I am an untrained model..."`.<br>`results/teacher_validation.json` does NOT exist. | **FAIL** | Teacher validation score missing; student outputs are fabricated/regex heuristics, not real model outputs. |
| **2.7** | Hidden test set: JSON validity >= 95% (2 marks) | Evaluated by grader | Untrained model scores 0.0%; regex parser scores 100.0%; actual trained Pythia-70M model output is missing. | **NOT TESTED** | Model weights must be trained and deployed. |
| **2.8** | Hidden test set: full-frame accuracy >= half teacher full-frame accuracy in `results/teacher_validation.json` (2 marks) | Evaluated by grader | Missing `teacher_validation.json` benchmark reference. | **NOT TESTED** | Teacher validation run is missing. |
| **2.9** | One page or less explanation in report covering: (a) sequence-level target, (b) logit-based target, (c) why logit-based not possible, (d) real limitation of approach (4 marks) | `report/report.pdf` | `report/report.pdf` is missing. | **FAIL** | Report has not been authored or compiled. |

---

### Task 3: The Inference Service in a Container (14 Marks)

| # | Requirement | Implementing File & Function | Verification Command & Actual Result | Status | Missing Evidence & Incomplete Tasks |
| :- | :--- | :--- | :--- | :---: | :--- |
| **3.1** | Service in `service/` on port 8000 with 3 endpoints: `POST /parse` (200 + 4-key JSON + headers `X-Model-Version` & `X-Served-By`), `GET /healthz` (200), `GET /readyz` (503 until loaded, 200 after) (2 marks) | Current: `service/app.py`<br>Old image: `command-parser-service:latest` | `service/app.py` runs on **port 8080**, NOT 8000.<br>`/readyz` returns 200 unconditionally, never 503 while loading. | **FAIL** | Port mismatch (8080 vs 8000); readiness probe does not track model loading state. |
| **3.2** | With `FAULT_INJECT=1`, `/parse` returns HTTP 500 with exact body `{"error": "invalid_model_output"}` (2 marks) | Current: `service/app.py`<br>Old image: `command-parser-service:latest:app.py:161` | `service/app.py` has **no `FAULT_INJECT` handling** and **no schema validation check** returning HTTP 500.<br>(Old image had it; current workspace code does not). | **FAIL** | `FAULT_INJECT` variable and output validation error handling are completely missing in `service/app.py`. |
| **3.3** | Model downloaded from object storage at start-up; image contains no weights (2 marks) | Current: `service/parser.py`<br>Old image: `command-parser-service:latest:download_model()` | Current `service/parser.py` is pure regex; downloads nothing from S3. | **FAIL** | Startup S3 download is not implemented in current workspace service. |
| **3.4** | Config from 4 env vars (`MODEL_URI`, `MODEL_VERSION`, `S3_ENDPOINT`, `MAX_NEW_TOKENS`); credentials only from Secret (2 marks) | `service/app.py:21-24` | `MODEL_URI`, `S3_ENDPOINT`, and `MAX_NEW_TOKENS` are NOT read in `service/app.py`. | **FAIL** | 3 of the 4 required environment variables are completely omitted. |
| **3.5** | Container builds from fresh clone with one command, pinned dependencies, <= 2 GB (3 marks) | `Dockerfile`<br>`Makefile:89-90` | `Dockerfile` copies optional `requirements.txt*`. There is no `requirements.txt` in workspace! No dependencies are pinned. | **FAIL** | Missing `requirements.txt` with pinned versions (`torch`, `transformers`, `fastapi`, `uvicorn`, `boto3`). |
| **3.6** | 50 requests complete at 1 CPU and 1 GiB memory limit with no OOM kill (2 marks) | `results/` | No benchmark script or output in `results/`. | **NOT TESTED** | 50-request sequential benchmark under resource limits was never executed or recorded. |
| **3.7** | Peak memory reported with command output as evidence (1 mark) | `results/` | No memory measurement command output. | **FAIL** | Missing peak memory command output evidence. |

---

### Task 4: Kubernetes Deployment, Scaling, and Reliability (22 Marks)

| # | Requirement | Implementing File & Function | Verification Command & Actual Result | Status | Missing Evidence & Incomplete Tasks |
| :- | :--- | :--- | :--- | :---: | :--- |
| **4.1** | Namespace `app`, Deployment (2 replicas), Service, Ingress routing `/parse` to Service (4 marks) | `k8s/namespace.yaml`<br>`k8s/deployment.yaml`<br>`k8s/service.yaml`<br>`k8s/ingress.yaml` | `kubectl get all -n app`<br>Result: **No resources found in app namespace**.<br>Manifests exist, but ports are set to 8080 instead of 8000. Ingress routes `/` instead of `/parse`. | **FAIL** | Service is not currently deployed in `app` namespace; manifests have wrong port (8080 vs 8000). |
| **4.2** | Requests/limits set; Service has no ready endpoints while model is loading (4 marks) | `k8s/deployment.yaml:40-58` | In `deployment.yaml`, probes target port 8080. Since `readyz` returns 200 immediately, endpoints become ready before model is loaded. | **FAIL** | Readiness probe logic in app does not gate readiness during model loading. |
| **4.3** | HPA: min 1, max 2, target CPU 70%; evidence of scaling 1->2 under load and back to 1; document local cluster limitations (4 marks) | `k8s/hpa.yaml`<br>`results/` | Manifest exists (`k8s/hpa.yaml`). No evidence of scaling test or load execution in `results/`. | **NOT TESTED** | HPA scaling evidence (logs, `kubectl get hpa -w`) is completely missing. |
| **4.4** | Rolling update: update `MODEL_VERSION` & `MODEL_URI` from v1 to v2 during load test (<= 0.5% errors); rollback via `kubectl rollout undo` (v1 restored) (4 marks) | `k8s/deployment.yaml`<br>`results/` | No rolling update test run; no `v1` or `v2` models exist to update between; no Locust log attached. | **NOT TESTED** | Missing execution of rolling update, rollback, and error-rate log during test. |
| **4.5** | Pod recovery: delete 1 pod during load test, show replica count restored with <= 2% failed requests (2 marks) | `results/` | No recovery test evidence in `results/`. | **NOT TESTED** | Missing pod deletion log and Locust error rate during recovery. |
| **4.6** | Cold start: delete all pods, show log evidence of model download from S3, report median time from creation to Ready over 3 runs (2 marks) | `results/` | No cold start measurement logs or median calculation in `results/`. | **FAIL** | Missing 3 cold-start timings, pod creation timestamps, and download logs. |
| **4.7** | Load balancing: 2 Ready replicas, standard load test through Ingress, each replica serves >= 30% of requests (2 marks) | `results/loadtest_headers.json` | `results/loadtest_headers.json` does NOT exist. | **FAIL** | Load balancing test was never run through Ingress. |

---

### Task 5: Subnetting and Network Access Control (10 Marks)

| # | Requirement | Implementing File & Function | Verification Command & Actual Result | Status | Missing Evidence & Incomplete Tasks |
| :- | :--- | :--- | :--- | :---: | :--- |
| **5.1** | Subnet table in `network/subnets.md`: allocate `10.20.0.0/16` for app (1000 hosts), public (250 hosts), data (100 hosts), management (20 hosts), largest to smallest, showing network, prefix, usable range, broadcast, usable host count ($2^{32-\text{prefix}} - 2$), and working (4 marks) | `network/subnets.md` | `Get-Content network/subnets.md`<br>**Current file lists completely wrong subnets**: `10.20.1.0/24`, `10.20.2.0/24`, `10.20.5.0/24`, `10.20.10.0/24`.<br>App (1000 hosts) requires `/22`, Data (100 hosts) requires `/25`, Management (20 hosts) requires `/27`. Working is missing. | **FAIL** | 4 out of 4 subnets have incorrect CIDR prefixes and IP ranges; calculation working is missing. |
| **5.2** | Stateless NACL rules in `network/nacl.json`: Inbound blocks 198.51.100.0/24 entirely, allows TCP 80 & 443 anywhere, TCP 22 from management, app replies; Outbound allows TCP 8000 to app, client replies (4 marks) | `network/nacl.json` | `cloud_assignment/tools/nacl_sim.py network/nacl.json cloud_assignment/network/packets_sample.jsonl --check`<br>Sim passes 6/6 sample packets, **BUT code inspection reveals critical failures**:<br>- Does NOT allow TCP 80!<br>- Does NOT allow TCP 22 from management!<br>- Does NOT allow inbound app replies!<br>- Rule 100 only denies port 443 from 198.51.100.0/24 instead of all ports!<br>- Outbound rule 100 uses wrong CIDR (`10.20.1.0/24` instead of `10.20.0.0/22`). | **FAIL** (on assignment requirements; will fail hidden 20-packet test) | Rule file is hardcoded only to pass the 6 sample packets; violates the actual specification. |
| **5.3** | Technical explanation: why stateless NACL needs separate reply rules, and why rule order matters for 198.51.100.0/24 block (2 marks) | `network/subnets.md:21-29` | Inspected `network/subnets.md`. Contains only 4 brief bullet points without addressing why rule order matters for the 198.51.100.0/24 block over allow rules. | **FAIL** | Incomplete explanation. Missing the required rule ordering rationale. |

---

### Task 6: Reproducibility, Testing, and CI/CD (10 Marks)

| # | Requirement | Implementing File & Function | Verification Command & Actual Result | Status | Missing Evidence & Incomplete Tasks |
| :- | :--- | :--- | :--- | :---: | :--- |
| **6.1** | `make up` builds and deploys whole system in <= 3 commands; `make down` deletes cluster idempotently (3 marks) | `Makefile:37-68` | `make up` references `k3d` CLI which is not in system PATH. Cluster setup fails if k3d is not available. | **FAIL** | `make up` cannot execute cleanly out of the box on this machine without k3d configured. |
| **6.2** | GitHub Actions workflow (`.github/workflows/ci.yml`): linting -> unit tests (>= 3) -> model evaluation downloading model from GitHub Release -> quality gate `score.py --min-validity 95` (4 marks) | `.github/workflows/ci.yml` | Workflow exists and defines stages. However, model download step has fallback bypass if release is missing, and model evaluated is dummy heuristic. | **FAIL** | Real model evaluation from GitHub Release asset is bypassed. |
| **6.3** | Link in report to a failed CI run using deliberately bad model (2 marks) | `report/report.pdf` | Repository is not pushed to GitHub; no GitHub Actions runs exist; report does not exist. | **FAIL** | Missing failed CI run URL and report. |
| **6.4** | Secret scanning step (gitleaks) reporting 0 leaks, and `AI_USE.md` present (1 mark) | `AI_USE.md`<br>`.github/workflows/ci.yml:13-26` | `AI_USE.md` is present. Secret scanning step exists in `ci.yml`. | **PASS** | Run gitleaks locally or verify CI run. |

---

### Task 7: Performance, Cost, and Review (12 Marks)

| # | Requirement | Implementing File & Function | Verification Command & Actual Result | Status | Missing Evidence & Incomplete Tasks |
| :- | :--- | :--- | :--- | :---: | :--- |
| **7.1** | Standard Locust load test execution & evidence: 4 users, spawn-rate 4, 2 min runtime against deployment. Report p50, p95 (<= 5000ms), throughput, error rate (<= 1%), Pod CPU/RAM (`kubectl top pods`), cold start time. Attach `loadtest_stats.csv` and `loadtest_headers.json` (4 marks) | `results/` | Checked `results/`. Neither `loadtest_stats.csv` nor `loadtest_headers.json` exists. No benchmark logs exist. | **FAIL** | Load test was never executed against the deployment. |
| **7.2** | Cost calculation: using `rate_card.json`, estimate cost per 1,000 requests showing formula and arithmetic steps based on replica CPU/RAM limits and hourly throughput (3 marks) | `report/report.pdf` | No cost calculation exists in repository or report. | **FAIL** | Complete cost estimation missing. |
| **7.3** | SLO definition: target and window (one load test run), error budget in requests, and consumed budget (2 marks) | `report/report.pdf` | No SLO definition or error budget calculation in repository or report. | **FAIL** | Complete SLO specification missing. |
| **7.4** | Review table: all 6 domains filled with measured numbers, identified limitations, and proposed improvements (3 marks) | `report/report.pdf` | No review table exists. | **FAIL** | Missing architectural review table. |

---

### Submission Deliverables (Handout Section 8)

| # | Deliverable | Location / Specification | Status | Finding & Audit Result |
| :- | :--- | :--- | :---: | :--- |
| **S.1** | Handwritten Reflection PDF | `reflection/230101093.pdf` (exactly 3 pages, naming convention `<roll_number>.pdf`, scanned copy) | **FAIL** | File does NOT exist. `reflection/` is empty. |
| **S.2** | GitHub Repository | Code, tests, manifests, Dockerfile, network, CI | **FAIL** | Workspace is not a git repository (`fatal: not a git repository`). |
| **S.3** | Model Artefacts | GitHub Release asset with model weights, tokenizer, checksum | **FAIL** | No GitHub Release; no release asset. |
| **S.4** | Evidence in `results/` | Logs, `score.py` outputs, Locust outputs, command outputs | **FAIL** | Missing Locust CSV/JSON files, teacher score, cluster logs. |
| **S.5** | README.md | Build, deploy, test, tear down commands | **PASS** | `README.md` documents lifecycle commands. |
| **S.6** | Git Final Tag | Commit tagged `final` | **FAIL** | No Git repository exists; no commit; no tag. |
| **S.7** | Final Report PDF | `report/report.pdf` (max 8 pages, one section per task) | **FAIL** | File does NOT exist. `report/` is empty. |

---

## 2. In-Depth Forensic Investigation of Critical Areas

### 2.1 Model Artifacts (`models/v1/`, `models/v2/`, and Checksums)
- **Requirement:** Fine-tuned student model and tokenizer must be saved to SeaweedFS under `models/v1/` and `models/v2/`, with checksum saved as `models/v1/model.sha256`, and uploaded as a GitHub Release asset.
- **Current Workspace State:**
  - Directory `models/` is completely empty.
  - SeaweedFS S3 bucket `models` was inspected via filer API: `{"Entries": null, "EmptyFolder": true}`.
  - No `model.safetensors`, `tokenizer.json`, or `model.sha256` exists in `models/v1/` or `models/v2/`.
- **Finding:** A previous fine-tuning run existed in `C:\Users\SACHITH\Music\230101093\training\v1` (with `model.safetensors` of 281 MB and `model.sha256`), but **none of these files were copied, uploaded to SeaweedFS, or committed/released** for `CloudComputingMiniProject`.

### 2.2 Full 1,500-Record Training & Dataset Lineage
- **Requirement:** Teacher must label 3,000 commands into sharded files. `worker/clean.py` must filter invalid records, deduplicate, and write the first 1,500 records into `datasets/v1/train.jsonl` with SHA-256 in `train.sha256`. Pythia-70M must train on these 1,500 records.
- **Current Workspace State:**
  - `data/teacher_shards/shard-0.jsonl` contains only **2 lines** (`C0001` and `C0002`).
  - Neither `data/train.jsonl` nor `datasets/v1/train.jsonl` exists in the workspace or S3.
  - `training/loss.csv` contains 3 static lines (`1,2.4512`, `2,1.8340`, `3,1.2105`), but inspection of `training/train.py:252` reveals these are hardcoded placeholder values generated when PyTorch imports fail.
- **Finding:** The full 1,500-record training has **NOT been performed** in this workspace.

### 2.3 Concurrent Teacher Workers & Sharding
- **Requirement:** Write worker in `worker/` reading `SHARD_INDEX` and `SHARD_COUNT` env vars, partitioning `i % SHARD_COUNT == SHARD_INDEX`, writing `teacher_raw` to S3. Run at least 2 workers concurrently in `pipeline` namespace.
- **Current Workspace State:**
  - Workspace file `worker/distill.py` does **NOT** read `SHARD_INDEX` or `SHARD_COUNT`, does not perform remainder partitioning, and writes key `raw_response` instead of `teacher_raw`.
  - In Kubernetes namespace `pipeline`, two jobs `teacher-worker-0` and `teacher-worker-1` ran 2 days ago (duration: 3h37m) using an older image `command-parser-worker:latest`. That image contained a correct `worker.py` script and populated `shard-0.jsonl` (1,500 lines) and `shard-1.jsonl` (1,500 lines) in SeaweedFS bucket `datasets`.
- **Finding:** The work was executed in the cluster 2 days ago, but the code in `worker/distill.py` was replaced with a non-compliant version, and the Kubernetes job manifests were not saved in the repository.

### 2.4 Kubernetes Rollout and Rollback
- **Requirement:** During an active load test, update deployment from `v1` to `v2` (error rate <= 0.5%), then execute `kubectl rollout undo` to restore `v1` (`X-Model-Version: v1`).
- **Current Workspace State:**
  - The `app` namespace currently contains **zero pods, deployments, or services** (`No resources found in app namespace`).
  - No `v1` or `v2` model weights exist to mount or serve.
  - No rollout/rollback tests were recorded in `results/`.
- **Finding:** Completely incomplete and unexecuted.

### 2.5 Pod Recovery Under Load
- **Requirement:** Delete one pod while load test is running; demonstrate Kubernetes restores replica count with <= 2% request failures.
- **Current Workspace State:**
  - No load test or pod recovery logs exist in `results/`.
- **Finding:** Completely incomplete and unexecuted.

### 2.6 Cold Start Benchmarking
- **Requirement:** Delete all pods; measure time from pod creation to Ready over 3 runs; report the median; provide log evidence of model download from S3.
- **Current Workspace State:**
  - `service/app.py` does not download anything from S3.
  - No cold start logs or timing measurements exist in `results/`.
- **Finding:** Completely incomplete and unexecuted.

### 2.7 50-Request Benchmark Under Resource Limits
- **Requirement:** Send 50 sequential requests to the container running with CPU limit 1 core and memory limit 1 GiB. Report peak memory observed with command output as evidence.
- **Current Workspace State:**
  - No memory benchmark script, command output, or measurement log exists in `results/`.
- **Finding:** Completely incomplete and unexecuted.

### 2.8 Locust Load Test Results
- **Requirement:** Run standard command:  
  `locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/loadtest`  
  Attach `results/loadtest_stats.csv` and `results/loadtest_headers.json`.
- **Current Workspace State:**
  - Locust is not installed in `.venv`.
  - Neither `loadtest_stats.csv` nor `loadtest_headers.json` exists in `results/`.
- **Finding:** Completely incomplete and unexecuted.

### 2.9 Cost Calculation and SLO
- **Requirement:** Using `rate_card.json` (vCPU = ₹3.50/hr, GiB = ₹0.45/hr), calculate cost of 1,000 requests using replica CPU/memory limits and requests per hour. Define SLO, window, and error budget.
- **Current Workspace State:**
  - No cost calculation, SLO formula, or error budget derivation exists anywhere in the repository or report.
- **Finding:** Completely missing.

### 2.10 Final Report & Reflection Documents
- **Requirement:**
  1. `report/report.pdf`: max 8 pages, one section per task, covering architecture, setup, decisions, results, limitations, improvements.
  2. `reflection/230101093.pdf`: exactly 3 pages, handwritten scanned reflections, with GitHub repo link, name, and roll number.
- **Current Workspace State:**
  - `report/` is completely empty (no `report.pdf`).
  - `reflection/` is completely empty (no `230101093.pdf`).
- **Finding:** Missing critical submission deliverables worth substantial penalty/zero mark triggers.

---

## 3. Discrepancy & Synthetic Artifact Analysis

During code inspection, several severe discrepancies and synthetic artifacts were discovered:

### 1. Synthetic Predictions in `results/`
- `results/predictions.jsonl` was NOT produced by Pythia-70M. Inspection of `evaluation/evaluate.py:82-86` confirms it was generated by running the regex heuristic `service.parser.CommandParser`.
- `results/untrained_student_predictions.jsonl` contains lines like:
  ```json
  {"id": "V001", "prediction": "I am an untrained model trying to parse remove the"}
  ```
  This is a hardcoded mock string created by `evaluation/evaluate.py:81`, not actual untrained language model output.
- `results/teacher_validation.json` does not exist in `results/`.

### 2. Service Code Regression in `service/`
- The Docker image `command-parser-service:latest` (built 2 days ago) contains a full FastAPI implementation (`/app/app.py` in container) with S3 download, `FAULT_INJECT`, schema checking, `MODEL_URI`, `S3_ENDPOINT`, `MAX_NEW_TOKENS`, and port 8000.
- However, the local workspace file `service/app.py` was replaced with a basic `http.server` running on port 8080 that does not load models, ignores S3, omits `FAULT_INJECT`, and uses regex parsing.

### 3. Subnet Architecture Inconsistencies
- The assignment specifies allocating `10.20.0.0/16` for:
  - App: 1,000 hosts $\implies$ **/22** (`10.20.0.0/22`, usable: 10.20.0.1 – 10.20.3.254, broadcast: 10.20.3.255, 1022 hosts)
  - Public: 250 hosts $\implies$ **/24** (`10.20.4.0/24`, usable: 10.20.4.1 – 10.20.4.254, broadcast: 10.20.4.255, 254 hosts)
  - Data: 100 hosts $\implies$ **/25** (`10.20.5.0/25`, usable: 10.20.5.1 – 10.20.5.126, broadcast: 10.20.5.127, 126 hosts)
  - Management: 20 hosts $\implies$ **/27** (`10.20.5.128/27`, usable: 10.20.5.129 – 10.20.5.158, broadcast: 10.20.5.159, 30 hosts)
- `network/subnets.md` incorrectly assigns `/24` to all four subnets with arbitrary addresses (`10.20.1.0/24`, `10.20.2.0/24`, `10.20.5.0/24`, `10.20.10.0/24`), completely failing the allocation rules.

### 4. NACL Rule Vulnerability
- In `network/nacl.json`, rules were hardcoded to pass only the 6 sample packets in `packets_sample.jsonl`.
- The rules completely omit TCP 80, TCP 22 (SSH from management), and inbound app replies, and only block port 443 from `198.51.100.0/24`. On the hidden 20-packet test, this will suffer a severe score reduction.

---

## 4. Missing Files Inventory

The following required files are currently missing from `CloudComputingMiniProject`:

1. `data/train.jsonl` and `data/train.sha256` (or `datasets/v1/train.jsonl`)
2. `models/v1/model.safetensors` (or PyTorch weights)
3. `models/v1/tokenizer.json` and tokenizer config
4. `models/v1/model.sha256`
5. `models/v2/` model and tokenizer files
6. `results/teacher_validation.json`
7. `results/loadtest_stats.csv`
8. `results/loadtest_headers.json`
9. `results/cold_start_logs.txt`
10. `results/recovery_test_stats.csv`
11. `results/rolling_update_stats.csv`
12. `report/report.pdf` (max 8 pages)
13. `reflection/230101093.pdf` (scanned 3-page handwritten document)
14. `.git/` repository initialization and tag `final`

---

## 5. Actionable Remediation Checklist

To achieve full assignment compliance and maximize marks, complete the following steps in sequence:

### Step 1: Data Cleaning & Shard Extraction
- Download `datasets/teacher/shard-0.jsonl` and `shard-1.jsonl` from SeaweedFS to `data/teacher_shards/`.
- Update `worker/clean.py` to ingest both shards, execute filtering rules (a)-(e), deduplicate by lowest numeric ID, and write verified records to `data/train.jsonl` and `data/train.sha256`.
- Record full cleaning counts in the report table.

### Step 2: Student Fine-Tuning & Model Publishing
- Fix `training/config.yaml` to include `max_seq_length: 128` and library versions (`torch: 2.x`, `transformers: 4.x`).
- Integrate actual trained model weights into `models/v1/` and `models/v2/`.
- Generate SHA-256 checksums (`models/v1/model.sha256`).
- Upload `models/v1/` and `models/v2/` to SeaweedFS bucket `models`.

### Step 3: Service Synchronization & Container Build
- Replace `service/app.py` with the FastAPI implementation from `command-parser-service:latest` (including S3 download, port 8000, `FAULT_INJECT`, `/readyz` 503 gating, `MODEL_URI`, `S3_ENDPOINT`, `MAX_NEW_TOKENS`).
- Create `requirements.txt` with pinned versions (`torch`, `transformers`, `fastapi`, `uvicorn`, `boto3`).
- Rebuild container image and verify image size is under 2 GB.
- Update `k8s/deployment.yaml`, `k8s/service.yaml`, and `k8s/ingress.yaml` to use port 8000.

### Step 4: Network & Subnet Corrections
- Overwrite `network/subnets.md` with mathematically correct CIDR allocations (`/22`, `/24`, `/25`, `/27`), all 5 values per subnet, full arithmetic working, and the half-page explanation of stateless replies and deny-rule precedence.
- Update `network/nacl.json` to include:
  - Inbound: Deny all from `198.51.100.0/24`; allow TCP 80 & 443; allow TCP 22 from `10.20.5.128/27`; allow TCP 1024-65535 from `10.20.0.0/22`.
  - Outbound: Allow TCP 8000 to `10.20.0.0/22`; allow TCP 1024-65535 to `0.0.0.0/0`.

### Step 5: Kubernetes Cluster Experiments
- Deploy manifests: `kubectl apply -f k8s/`.
- Run Locust load test through Ingress and record `loadtest_stats.csv` and `loadtest_headers.json`.
- Execute rolling update from `v1` to `v2` during load, followed by `kubectl rollout undo`.
- Execute pod recovery test and cold start benchmark (3 runs, record median).
- Execute 50-request memory limit test (1 CPU, 1 GiB) and capture `docker stats` / `kubectl top`.

### Step 6: Evaluation & Score Reports
- Run `cloud_assignment/tools/score.py` on the real teacher predictions, untrained Pythia-70M, and trained student model against `cloud_assignment/data/validation.jsonl`.
- Save `results/teacher_validation.json` and student score reports.

### Step 7: Final Deliverables Compilation
- Calculate cost per 1,000 requests using `rate_card.json` formula.
- Define SLO, error budget, and complete the 6-row architectural review table.
- Compile `report/report.pdf` (max 8 pages).
- Scan and place handwritten reflection at `reflection/230101093.pdf`.
- Initialize Git repository, commit all files, create GitHub release with model assets, run CI workflow, and tag commit as `final`.

