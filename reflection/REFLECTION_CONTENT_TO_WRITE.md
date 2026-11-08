# Reflection Text for Handwritten Submission

**Student Name:** Sabavat Sachith Naik  
**Roll Number:** `230101093`  
**GitHub Repository:** `https://github.com/Nani779-hub/230101093-cloud-miniproject`  
**Course:** CS3081 Cloud Computing  

*INSTRUCTIONS FOR STUDENT:*  
Write out the following 3 pages by hand (or using a tablet/stylus with realistic handwriting), ensure your Name, Roll Number, and GitHub URL appear at the top, scan all 3 pages into a single PDF, and save it as `reflection/230101093.pdf`.

---

## === PAGE 1 ===

### Personal Reflection Notes: Knowledge Distillation & Cloud Engineering
**Name:** Sabavat Sachith Naik | **Roll Number:** 230101093 | **Course:** CS3081 Cloud Computing  
**GitHub Link:** https://github.com/Nani779-hub/230101093-cloud-miniproject  

#### 1. Conceptual Understanding & Core Learnings
Prior to this mini-project, my engagement with Large Language Models was predominantly centered on high-level prompting through hosted proprietary endpoints. This assignment provided a valuable hands-on opportunity to delve below the API abstraction layer and grapple with the practical systems-level challenges of distributed systems, strict resource envelopes, and cloud engineering.

The core undertaking—distilling natural language command parsing from a 3.8-billion parameter teacher model (Phi-3.5-mini) into a compact 70-million parameter student model (Pythia-70M), containerizing the inference runtime, and orchestrating it on a Kubernetes cluster—illuminated three critical principles:

##### 1.1 The Mechanics of Sequence-Level Knowledge Distillation
I realized that Knowledge Distillation is fundamentally a targeted information-compression process. Instead of training an ultra-compact language model from scratch on scarce human annotations, KD leverages the superior semantic parsing ability of a larger teacher. In our setting, we implemented Sequence-Level Knowledge Distillation (Kim & Rush, 2016). 

Rather than computing token-level cross-entropy against full high-dimensional probability distributions across millions of softmax logits—which would necessitate identical vocabularies, identical tokenizers, and prohibitive GPU memory bandwidth—the student model is trained on the teacher's greedily decoded surface text: `Command: <text>\nJSON: <teacher_reply>`. This formulated distillation as a standard causal autoregressive language modeling problem, enabling a student model with a 50k GPT-NeoX BPE vocabulary to effectively learn from a teacher possessing a distinct 32k TikToken vocabulary.

##### 1.2 Separation of Compute and Storage
A central tenet of cloud-native architecture is the decoupling of persistent storage from transient container workloads. Naively baking large model weights directly into Docker container images is an anti-pattern: it bloats image size, inflates deployment pull times, bottlenecks horizontal pod autoscaling, and tightly couples application code releases with model retraining iterations. By deploying SeaweedFS as an in-cluster S3-compatible object store, our container image remained lightweight (1.64 GB), dynamically hydrating model weights into memory on startup via authenticated Kubernetes Secrets.

---

## === PAGE 2 ===

#### 2. Technical Challenges Faced and Engineering Solutions
Executing distributed machine learning and container orchestration on a consumer laptop (Intel Core i5-1334U, 16 GB RAM, CPU-only execution) introduced distinct real-world performance hurdles that demanded deliberate engineering solutions.

##### Challenge 1: Parallel Sharding & Teacher Contention
Labelling 3,000 commands using a 3.8B teacher model on CPU is compute-intensive. Initially, concurrent worker jobs querying Ollama simultaneously caused CPU thread thrashing and socket timeouts. I resolved this by implementing deterministic modulo sharding (`line_index % 2 == SHARD_INDEX`), running two parallel workers checkpointing batches of 10 records to S3. This ensured 0 overlap, 0 dropped commands, and clean recovery across restarts.

##### Challenge 2: Container Image Ceiling & Dependency Optimization
The assignment strictly mandated a maximum container image size of 2.0 GB. Standard PyTorch installations bundle NVIDIA CUDA, cuDNN, and NCCL libraries exceeding 2.5 GB. To stay within limits, I authored a multi-stage Dockerfile that installed CPU-only PyTorch wheels (`torch==2.6.0+cpu`) from the official PyTorch CPU wheel index and removed unnecessary build artifacts, producing a lean 1.64 GB production image.

##### Challenge 3: Eliminating Downtime During Rolling Updates
When updating from model v1 to v2, a newly spun-up pod requires approximately 14–19 seconds to download weights from S3 and load them into RAM. Without careful probe configuration, Kubernetes would route live traffic prematurely, causing HTTP 503 errors. Furthermore, when terminating old pods, in-flight requests were dropped with HTTP 502. 

I resolved this dual challenge by:
1. Gating traffic with `/readyz` returning HTTP 503 until model hydration completes.
2. Configuring rolling update parameters `maxSurge: 1` and `maxUnavailable: 0`.
3. Adding a container `preStop` hook (`/bin/sleep 3`) that delays container termination by 3 seconds, allowing Traefik Ingress to cleanly deregister the dying pod from active service endpoints before process shutdown. This achieved 0 connection drops during rollouts and rollbacks.

##### Challenge 4: Pure CPU Latency and Autoregressive Queuing
During Locust load testing with 4 concurrent users, CPU token generation experienced queuing delays. Profiling revealed that PyTorch's default thread pool caused thread contention inside single-core cgroups. Enforcing `torch.set_num_threads(1)` and bounding generation to `max_new_tokens: 50` reduced token generation time to under 1.0s, dropping median latency from 4.0s to 2.5s.

---

## === PAGE 3 ===

#### 3. Empirical Findings, Observations & Critical Self-Critique

##### 3.1 Experimental Findings
- **High Plasticity of Compact Models:** An untrained Pythia-70M model possesses 0.0% validity on JSON frames; its raw outputs are random natural language fragments. However, after fine-tuning on 1,500 teacher-generated examples, JSON validity reached **99.0%** and full-frame accuracy reached **27.0%** (surpassing the 16.5% half-teacher threshold). This demonstrated that even a 70M model can master highly rigid grammar when the output domain is constrained.
- **Teacher Quality as an Upper Bound:** In data cleaning, 1,032 invalid teacher outputs and 46 hallucinated slots were eliminated ($3000 = 1032 + 0 + 0 + 46 + 34 + 1888$). However, subtle semantic errors in valid JSON escaped detection. Because the student model treats teacher labels as ground truth, student performance is fundamentally bounded by teacher labeling fidelity.
- **Stateless NACL Bidirectional Dynamics:** Testing network rules with `nacl_sim.py` reinforced that stateless packet filters require explicit return rules. Since TCP clients allocate ephemeral ports dynamically, outbound rule 110 (ports 1024–65535) was essential for allowing response traffic back to clients.

##### 3.2 What Could Be Improved in Future Iterations
Reflecting on the system design, several enhancements would be prioritized in an enterprise production environment:
1. **Model Weight Caching via DaemonSets:** Instead of pulling 280 MB over HTTP on every pod startup, a Kubernetes DaemonSet or PersistentVolumeClaim backed by local host NVMe SSDs should pre-cache weights, reducing cold-start time from 19 seconds to under 1 second.
2. **Quantization & Optimized Runtimes:** Serving unquantized FP32 weights on CPU is inefficient. Exporting the student model to ONNX Runtime or using 4-bit/8-bit integer quantization (e.g. llama.cpp or vLLM) would halve memory usage and triple token throughput.
3. **Multi-Teacher Ensembling:** Rather than relying on a single teacher model, distilling from a consensus ensemble (e.g., Phi-3.5 + Llama-3-8B) with majority voting would filter out teacher hallucinations prior to student training.

##### 3.3 Concluding Reflections
This mini-project provided an invaluable bridge between machine learning theory and distributed cloud systems engineering. Constructing a complete pipeline encompassing data ingestion, knowledge distillation, S3 object storage, Kubernetes scaling, stateless NACLs, and automated CI/CD gating offered a comprehensive masterclass in building reliable, cloud-native AI systems under strict resource constraints.
