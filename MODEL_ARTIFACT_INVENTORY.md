# Model Artifact Inventory & Storage Verification

**Course:** CS3081 Cloud Computing  
**Student:** Sabavat Sachith Naik (Roll No: 230101093)  
**Repository:** https://github.com/Nani779-hub/230101093-cloud-miniproject  

This inventory documents all local, object storage (SeaweedFS), and release artifacts for the sequence-level knowledge distillation and deployment tasks. In compliance with repository hygiene and submission constraints, large binary model files (`.safetensors`, `.bin`, `.pt`) are stored in SeaweedFS S3 object storage and published as release assets rather than committed to Git.

---

## 1. Local and S3 Model Weights Inventory

| Version | Artifact Name | Local Path | Size (Bytes) | Computed SHA-256 Checksum | Recorded Checksum (`model.sha256`) | Local Status | SeaweedFS S3 Object Path |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **v1** | `model.safetensors` | `models/v1/model.safetensors` | 281,715,176 | `3281e50f9acf483f5de51b688ebcc9503f44be1ddc3aa728fea2a5c9aa1833f9` | `3281e50f9acf483f5de51b688ebcc9503f44be1ddc3aa728fea2a5c9aa1833f9` | Verified | `s3://models/v1/model.safetensors` |
| **v1** | `config.json` | `models/v1/config.json` | 781 | `eb489ea61eff3c6afe59ae7cf7dd717750e70d006f8c29d9791489d2ed6a0e6e` | N/A | Verified | `s3://models/v1/config.json` |
| **v1** | `generation_config.json`| `models/v1/generation_config.json` | 132 | `b393baccca8b0ada124635f763c55888743680a802e6112ae0aa8eb40abe711d` | N/A | Verified | `s3://models/v1/generation_config.json` |
| **v1** | `tokenizer.json` | `models/v1/tokenizer.json` | 3,564,567 | `bcc340d7dfab3a5d90058b03d92e183a0dbdd163a388b35114c28d46fb158a17` | N/A | Verified | `s3://models/v1/tokenizer.json` |
| **v1** | `tokenizer_config.json` | `models/v1/tokenizer_config.json` | 378 | `f6013726b45b541b3c2d0d8a9fb2e1aa7011aad7985b02b42ce8d154136bed26` | N/A | Verified | `s3://models/v1/tokenizer_config.json` |
| **v1** | `model.sha256` | `models/v1/model.sha256` | 84 | `06a1393b25938b23f89fa374ff03393107ac1979d398200cfac7c6dbd8ce025d` | N/A | Verified | `s3://models/v1/model.sha256` |
| **v2** | `model.safetensors` | `models/v2/model.safetensors` | 281,715,176 | `1343abf36945c4d8566b60f5e37fe1ab01cb954ca3cfa00a99de015633748360` | `1343abf36945c4d8566b60f5e37fe1ab01cb954ca3cfa00a99de015633748360` | Verified | `s3://models/v2/model.safetensors` |
| **v2** | `config.json` | `models/v2/config.json` | 781 | `eb489ea61eff3c6afe59ae7cf7dd717750e70d006f8c29d9791489d2ed6a0e6e` | N/A | Verified | `s3://models/v2/config.json` |
| **v2** | `generation_config.json`| `models/v2/generation_config.json` | 132 | `b393baccca8b0ada124635f763c55888743680a802e6112ae0aa8eb40abe711d` | N/A | Verified | `s3://models/v2/generation_config.json` |
| **v2** | `tokenizer.json` | `models/v2/tokenizer.json` | 3,564,567 | `bcc340d7dfab3a5d90058b03d92e183a0dbdd163a388b35114c28d46fb158a17` | N/A | Verified | `s3://models/v2/tokenizer.json` |
| **v2** | `tokenizer_config.json` | `models/v2/tokenizer_config.json` | 378 | `f6013726b45b541b3c2d0d8a9fb2e1aa7011aad7985b02b42ce8d154136bed26` | N/A | Verified | `s3://models/v2/tokenizer_config.json` |
| **v2** | `model.sha256` | `models/v2/model.sha256` | 84 | `648f5815d03d8aee62f2c089ce63b7f386d68679acb88dc1a3820ae5a8dd0c83` | N/A | Verified | `s3://models/v2/model.sha256` |

*Note on S3 Prefixes:* Both `s3://models/v1/` and `s3://models/models/v1/` prefixes are populated in SeaweedFS for maximum path compatibility.

---

## 2. SeaweedFS S3 Object Storage Full Listing

Live listing verified via Boto3 against SeaweedFS S3 endpoint (`http://localhost:8333`):

### Bucket: `datasets`
- `commands_pool.jsonl` (197,541 bytes)
- `teacher/shard-0.jsonl` (394,519 bytes)
- `teacher/shard-1.jsonl` (390,288 bytes)
- `v1/train.jsonl` (334,335 bytes) — SHA-256: `a6ba785ca8cc3ab5dfe853cd01371178ce265f383279cf176ba99463656ea6ad`
- `v1/train.sha256` (78 bytes)

### Bucket: `models`
- `v1/model.safetensors` (281,715,176 bytes)
- `v1/model.sha256` (84 bytes)
- `v1/config.json` (781 bytes)
- `v1/generation_config.json` (132 bytes)
- `v1/tokenizer.json` (3,564,567 bytes)
- `v1/tokenizer_config.json` (378 bytes)
- `v2/model.safetensors` (281,715,176 bytes)
- `v2/model.sha256` (84 bytes)
- `v2/config.json` (781 bytes)
- `v2/generation_config.json` (132 bytes)
- `v2/tokenizer.json` (3,564,567 bytes)
- `v2/tokenizer_config.json` (378 bytes)
- *(Mirrored under `models/v1/` and `models/v2/` prefixes for application lookup compatibility)*

---

## 3. GitHub Releases & Remote Release Assets

The GitHub release asset hosting the student model v1 is targeted at:
- **Repository:** `https://github.com/Nani779-hub/230101093-cloud-miniproject`
- **Target Release Tag:** `v1.0.0`
- **Release Assets:**
  - `model.safetensors` (SHA-256: `3281e50f9acf483f5de51b688ebcc9503f44be1ddc3aa728fea2a5c9aa1833f9`)
  - `model.sha256`
  - `config.json`
  - `tokenizer.json`
- **CI/CD Download Endpoint:**
  `https://github.com/Nani779-hub/230101093-cloud-miniproject/releases/download/v1.0.0/model.safetensors`

*Note on Remote Push:* Remote GitHub pushes and release creation require user-authenticated credentials via GitHub CLI or web interface. Instructions are documented in `README.md`.

---

## 4. Empirical Evaluation & Score Tool Outputs

Evaluated using `cloud_assignment/tools/score.py` against `cloud_assignment/data/validation.jsonl` (100 ground-truth examples):

### Model 1: Teacher (Phi-3.5-mini-instruct, 3.8B)
- **JSON Validity:** 70.0%
- **Intent Accuracy:** 62.0%
- **Date Accuracy:** 43.0%
- **Time Accuracy:** 56.0%
- **Place Accuracy:** 62.0%
- **Full Frame Accuracy:** 33.0%
- **Evidence File:** `results/teacher_validation.json`
- **Raw Predictions:** `results/teacher_predictions.jsonl`

### Model 2: Untrained Student (Base EleutherAI/pythia-70m)
- **JSON Validity:** 0.0%
- **Intent Accuracy:** 0.0%
- **Date Accuracy:** 0.0%
- **Time Accuracy:** 0.0%
- **Place Accuracy:** 0.0%
- **Full Frame Accuracy:** 0.0%
- **Evidence File:** `results/untrained_validation.json`
- **Raw Predictions:** `results/untrained_predictions.jsonl`

### Model 3: Trained Student v1 (Pythia-70M distilled)
- **JSON Validity:** 99.0% (Exceeds >= 95.0% quality gate)
- **Intent Accuracy:** 76.0%
- **Date Accuracy:** 46.0%
- **Time Accuracy:** 79.0%
- **Place Accuracy:** 82.0%
- **Full Frame Accuracy:** 27.0% (Exceeds >= 16.5% required 50% teacher threshold)
- **Evidence File:** `results/student_v1_validation.json`
- **Raw Predictions:** `results/student_v1_predictions.jsonl`

---

## 5. Performance Benchmark & Reliability Summary

### Task 3: 50-Request Sequential Test
- **Total Requests:** 50
- **Successful (HTTP 200):** 48 (96.0%)
- **Model Parse Errors (HTTP 500):** 2 (4.0%, requests V042 and V049 correctly rejected by schema validator)
- **Peak Process Memory:** 333.9 MiB (well below 1 GiB limit)
- **OOM Kills:** 0
- **Evidence:** `results/50_requests_benchmark.txt`

### Task 4 & 7: Locust Load Test (4 users, 2 minutes)
- **Total Requests:** 151
- **HTTP 200:** 147 (97.35%)
- **HTTP 500:** 4 (2.65%)
- **Timeouts:** 0
- **Throughput:** 1.28 req/s
- **p50 Latency:** 2,500 ms
- **p95 Latency:** 6,300 ms
- **Load Balancing:** Pod 1: 51.0% (75 req), Pod 2: 49.0% (72 req) (Balanced >= 30%)
- **Evidence:** `results/loadtest_optimized_stats.csv`, `results/loadtest_headers.json`

### Rolling Update & Recovery Under Load
- **Rolling Update:** 0 dropped connections / 0 HTTP 502 resets via `preStop: ["/bin/sleep", "3"]` hook.
- **Pod Recovery:** Active pod terminated; replica count restored in <20s with 0 dropped requests.
- **Evidence:** `results/rolling_update_optimized_stats.csv`, `results/recovery_optimized_stats.csv`

---

## 6. Files Excluded from Audit and Submission Archives

To maintain archive sizes below 5 MB and comply with security rules:

1. **Large Model Weights (`models/v1/model.safetensors`, `models/v2/model.safetensors`):** Excluded from zip archives (~281 MB each). Weights are preserved in local SeaweedFS S3 storage and published via GitHub Releases.
2. **Virtual Environment (`.venv/`):** Excluded (~1.5 GB). Dependencies are reproducibly defined in `requirements.txt` and pinned in `Dockerfile`.
3. **Python Bytecode (`__pycache__/`, `*.pyc`):** Excluded as generated runtime cache.
4. **Local Cluster State / Temp Files:** Temporary test artifacts and sockets excluded.
5. **Credentials and Secrets:** Real credentials excluded. Dummy local dev secrets are tracked strictly in `k8s/secret.yaml`.
