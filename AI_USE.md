# Statement of AI Use

**Student Roll Number:** 230101093  
**Course:** Cloud Computing  
**Project:** Cloud Computing Mini Project  

---

## 1. AI Tools and Models Utilized

1. **Ollama Local Runtime (`phi3.5:latest`)**:
   - **Role:** Teacher LLM for dataset labeling and knowledge distillation over 3,000 commands from `cloud_assignment/data/commands_pool.jsonl`.
   - **Configuration:** Local execution (offline, privacy-preserving), temperature 0, seed 42, strict JSON mode.
   - **Quantization:** Q4_0 (3.8B parameters), running on local CPU/iGPU (Intel Core i5-1334U, 16 GB RAM).

2. **AI Coding Assistant (Antigravity / Gemini)**:
   - **Role:** Interactive pair-programming assistant for project directory scaffolding, Makefile definitions, manifest formatting, and reviewing code against assignment constraints.
   - **Verification:** All generated configurations and code are manually inspected, validated with local unit tests, and verified against the assignment schema and scoring scripts.

---

## 2. Boundaries and Academic Integrity Compliance

- **Immutable Dataset:** `cloud_assignment/data/validation.jsonl` was never used in training, distillation, or prompting. It is reserved strictly for evaluation.
- **Original Assignment Kit:** `cloud_assignment/` has been preserved without modifications.
- **No Synthetic / Fabricated Benchmarks:** No simulated or fake results, reports, or teacher outputs were committed. All numbers in `results/` and `report/` correspond to genuine local runs.
- **Reflection:** The final reflection document (`reflection/230101093.pdf`) is written by hand by the student, scanned, and added directly without automated generation.

