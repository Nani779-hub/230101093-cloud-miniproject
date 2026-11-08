#!/usr/bin/env python3
"""
Generate the official academic report for Cloud Computing Mini Project (CS3081).
Roll Number: 230101093
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_PDF = os.path.join(SCRIPT_DIR, "report.pdf")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y' on all pages."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setFillColor(colors.HexColor("#64748B"))

        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 11 * 72 - 36, "CS3081 Cloud Computing — Knowledge Distillation & Cloud Deployment")
            self.drawRightString(8.5 * 72 - 54, 11 * 72 - 36, "Roll No: 230101093")
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

        # Footer (all pages)
        self.setLineWidth(0.5)
        self.line(54, 45, 8.5 * 72 - 54, 45)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 32, page_str)
        self.drawString(54, 32, "Academic Mini Project Submission — CS3081 Cloud Computing")
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#475569'),
        spaceAfter=6,
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=7,
        spaceAfter=2.5,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#334155'),
        spaceBefore=3.5,
        spaceAfter=2,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=7.6,
        leading=9.8,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=2.5,
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.0,
        leading=8.8,
        textColor=colors.HexColor('#1E293B'),
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell,
        fontName='Helvetica-Bold',
    )
    table_cell_header = ParagraphStyle(
        'TableHeader',
        parent=table_cell,
        fontName='Helvetica-Bold',
        textColor=colors.white,
    )

    story = []

    # Title Banner
    story.append(Paragraph("Knowledge Distillation and Cloud-Native Deployment of a Lightweight Command-Parsing Language Model", title_style))
    story.append(Paragraph("<b>Course:</b> CS3081 Cloud Computing &nbsp;|&nbsp; <b>Student:</b> Sabavat Sachith Naik (Roll: 230101093)<br/><b>GitHub Repository:</b> <u>https://github.com/Nani779-hub/230101093-cloud-miniproject</u>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=5))

    # Executive Summary
    story.append(Paragraph("<b>Executive Summary:</b> This project implements an end-to-end, resource-constrained sequence-level knowledge distillation pipeline and production-grade cloud microservice architecture. A high-parameter teacher model (Phi-3.5-mini-instruct, 3.8B parameters) was leveraged to generate semantic parse representations (intent, date, time, and place) for 3,000 commands from the SLURP benchmark. Teacher outputs were parallel-ingested via sharded Kubernetes workers into SeaweedFS S3-compatible object storage, cleaned, and verified against strict accounting identities. The resulting dataset was utilized to fine-tune an EleutherAI/Pythia-70M student model on pure CPU hardware. The student model was subsequently containerized into a minimal (&lt;1.65 GB) FastAPI service, deployed on a multi-replica local k3d Kubernetes cluster with HPA autoscaling, zero-downtime rolling updates, health probes, and stateless Network Access Control Lists (NACLs), rigorously validated under CI/CD, and benchmarked under Locust load testing.", body_style))
    story.append(Spacer(1, 2))

    # ─────────────────────────────────────────────────────────────────────────────
    # TASK 1
    # ─────────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("1. Task 1: Object Storage and Parallel Teacher Labelling", h1_style))
    story.append(Paragraph("<b>Architecture &amp; Storage Setup:</b> A local lightweight Kubernetes cluster was deployed via <code>cluster/k3d.yaml</code> with host-forwarded ports for HTTP/HTTPS ingress (8080) and S3 object storage (8333). Inside the <code>data</code> namespace, SeaweedFS was provisioned providing S3-compliant object storage with buckets <code>datasets</code> and <code>models</code>. The unlabelled pool of 3,000 natural language commands was uploaded to <code>s3://datasets/commands_pool.jsonl</code>. The teacher model (Phi-3.5-mini, 3.8B parameters) was served locally via Ollama with fixed hyperparameters (<code>temperature=0</code>, <code>seed=42</code>). A system prompt (<code>prompts/teacher_prompt.txt</code>) strictly constrained the output to a four-key JSON frame: <code>intent</code>, <code>date</code>, <code>time</code>, and <code>place</code> across the eight SLURP intents (<code>alarm_set</code>, <code>alarm_query</code>, <code>calendar_set</code>, <code>calendar_query</code>, <code>calendar_remove</code>, <code>weather_query</code>, <code>datetime_query</code>, <code>recommendation_events</code>).", body_style))
    story.append(Paragraph("<b>Parallel Sharding Strategy:</b> To distribute workload without inter-worker coordination or locking, deterministic modulus sharding was implemented: worker <i>k</i> out of <i>N</i> processes record <i>i</i> if <code>i mod N == k</code>. Two independent Kubernetes Jobs (<code>teacher-worker-0</code> and <code>teacher-worker-1</code>) ran concurrently in the <code>pipeline</code> namespace, each processing 1,500 commands and checkpointing outputs to <code>s3://datasets/teacher/shard-0.jsonl</code> and <code>shard-1.jsonl</code> every 10 records. Shard accounting verified exactly 1,500 unique commands per shard with zero overlap and zero gaps across the 3,000 commands.", body_style))

    # Cleaning Table
    story.append(Paragraph("<b>Data Cleaning &amp; Quality Gate (clean.py):</b> Shards were merged and sanitized against criteria (a) through (e). The strict mathematical identity <code>input = (a) + (b) + (c) + (d) + duplicates + kept</code> (3000 = 1032 + 0 + 0 + 46 + 34 + 1888) was verified:", body_style))

    clean_data = [
        [Paragraph("Category / Reason", table_cell_header), Paragraph("Count", table_cell_header), Paragraph("Percentage", table_cell_header), Paragraph("Description / Action", table_cell_header)],
        [Paragraph("Total Input Records", table_cell_bold), Paragraph("3,000", table_cell), Paragraph("100.0%", table_cell), Paragraph("Combined lines across shard-0 and shard-1", table_cell)],
        [Paragraph("(a) Invalid JSON", table_cell), Paragraph("1,032", table_cell), Paragraph("34.4%", table_cell), Paragraph("Model returned malformed syntax, truncated braces, or non-JSON", table_cell)],
        [Paragraph("(b) Wrong Keys", table_cell), Paragraph("0", table_cell), Paragraph("0.0%", table_cell), Paragraph("Missing required keys or containing extraneous keys", table_cell)],
        [Paragraph("(c) Invalid Intent", table_cell), Paragraph("0", table_cell), Paragraph("0.0%", table_cell), Paragraph("Intent outside the eight sanctioned assignment intents", table_cell)],
        [Paragraph("(d) Hallucinated Slots", table_cell), Paragraph("46", table_cell), Paragraph("1.5%", table_cell), Paragraph("Slot text not verbatim present in natural language input command", table_cell)],
        [Paragraph("(e) Duplicate Commands", table_cell), Paragraph("34", table_cell), Paragraph("1.1%", table_cell), Paragraph("Redundant utterances; retained entry with smallest command ID", table_cell)],
        [Paragraph("Valid Clean Records Kept", table_cell_bold), Paragraph("1,888", table_cell_bold), Paragraph("62.9%", table_cell_bold), Paragraph("Preserved in ID order; saved to datasets/v1/train.jsonl", table_cell_bold)],
    ]
    t_clean = Table(clean_data, colWidths=[115, 45, 55, 290])
    t_clean.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_clean)
    story.append(Spacer(1, 2))
    story.append(Paragraph("<b>SHA-256 Checksum:</b> Cleaned dataset was uploaded to <code>s3://datasets/v1/train.jsonl</code> with hash <code>a6ba785ca8cc3ab5dfe853cd01371178ce265f383279cf176ba99463656ea6ad</code>, saved in <code>datasets/v1/train.sha256</code> and <code>data/train.sha256</code> with Unix LF formatting.", body_style))
    story.append(Spacer(1, 2))

    # ─────────────────────────────────────────────────────────────────────────────
    # TASK 2
    # ─────────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("2. Task 2: Training the Student (Sequence-Level Distillation)", h1_style))
    story.append(Paragraph("<b>Motivation &amp; Distillation Theory:</b> Deploying modern LLMs (&gt;3B parameters) on low-power edge nodes induces prohibitive memory footprints and latency bottlenecks. Sequence-Level Knowledge Distillation (Kim &amp; Rush, EMNLP 2016) mitigates this by training a compact student model (Pythia-70M, 70M parameters) directly on teacher-generated natural language sequences: <code>Command: &lt;text&gt;\\nJSON: &lt;teacher_reply&gt;</code>. In contrast to token-level or logit-based distillation (which minimizes Kullback-Leibler divergence over full teacher softmax distributions P_T(y_t | y_{&lt;t}, x)), sequence-level distillation requires only the teacher's greedily decoded surface outputs y* = argmax_y P_T(y|x).", body_style))
    story.append(Paragraph("<b>Why Logit-Based Distillation is Infeasible Here:</b> (1) The teacher model (Phi-3.5, vocabulary size 32,064) and student model (Pythia-70M, vocabulary size 50,304) possess non-aligned token vocabularies and differing subword tokenizers (TikToken BPE vs. GPT-NeoX BPE), making direct per-token cross-entropy alignment mathematically non-trivial. (2) Standard inference runtimes (such as Ollama REST API) expose generated text tokens rather than raw logit distribution tensors across all 32,000+ dimensions. (3) Sequence-level cross-entropy loss on teacher outputs avoids the massive memory transfer overhead of saving full probability distributions.", body_style))
    story.append(Paragraph("<b>Implementation &amp; Hyperparameters:</b> As specified in <code>training/config.yaml</code>, training was executed on CPU using PyTorch and Hugging Face Transformers with seed 42, AdamW optimizer (learning rate 5.0e-5, weight decay 0.01), batch size 8, sequence length 80, linear warmup, and gradient clipping at 1.0. Measured epoch loss from <code>training/loss.csv</code> confirmed monotonic convergence: Version 1 (5 epochs on 1,500 records) decreased from 2.2158 to 0.2915 (2.2158 -&gt; 0.8992 -&gt; 0.5757 -&gt; 0.4162 -&gt; 0.2915); Version 2 converged to 0.1716 at epoch 7 (... -&gt; 0.2213 -&gt; 0.1716). Both versions were uploaded to SeaweedFS under <code>models/v1/</code> and <code>models/v2/</code>.", body_style))

    # Evaluation Table
    story.append(Paragraph("<b>Genuine Empirical Evaluation on validation.jsonl (100 Commands):</b>", h2_style))
    eval_data = [
        [Paragraph("Model", table_cell_header), Paragraph("Parameters", table_cell_header), Paragraph("JSON Validity", table_cell_header), Paragraph("Intent Acc.", table_cell_header), Paragraph("Date Acc.", table_cell_header), Paragraph("Time Acc.", table_cell_header), Paragraph("Place Acc.", table_cell_header), Paragraph("Full Frame", table_cell_header)],
        [Paragraph("Teacher (Phi-3.5-mini)", table_cell_bold), Paragraph("3.8 B", table_cell), Paragraph("70.0%", table_cell), Paragraph("62.0%", table_cell), Paragraph("59.0%", table_cell), Paragraph("62.0%", table_cell), Paragraph("53.0%", table_cell), Paragraph("33.0%", table_cell_bold)],
        [Paragraph("Untrained Student (Pythia-70M)", table_cell), Paragraph("70 M", table_cell), Paragraph("0.0%", table_cell), Paragraph("0.0%", table_cell), Paragraph("0.0%", table_cell), Paragraph("0.0%", table_cell), Paragraph("0.0%", table_cell), Paragraph("0.0%", table_cell)],
        [Paragraph("Trained Student v1 (5 epochs)", table_cell_bold), Paragraph("70 M", table_cell), Paragraph("99.0%", table_cell_bold), Paragraph("76.0%", table_cell_bold), Paragraph("46.0%", table_cell), Paragraph("79.0%", table_cell), Paragraph("82.0%", table_cell), Paragraph("27.0%", table_cell_bold)],
        [Paragraph("Trained Student v2 (7 epochs)", table_cell), Paragraph("70 M", table_cell), Paragraph("94.0%", table_cell), Paragraph("72.0%", table_cell), Paragraph("60.0%", table_cell), Paragraph("79.0%", table_cell), Paragraph("83.0%", table_cell), Paragraph("40.0%", table_cell_bold)],
    ]
    t_eval = Table(eval_data, colWidths=[115, 50, 55, 55, 55, 55, 55, 65])
    t_eval.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_eval)
    story.append(Spacer(1, 2))
    story.append(Paragraph("<b>Analysis &amp; Limitations:</b> Untrained Pythia-70M produces 0.0% valid JSON, as it lacks domain knowledge of structured syntax. Post-distillation, Student v1 JSON validity reaches <b>99.0%</b> (passing the &gt;= 95% quality gate) with <b>27.0%</b> full-frame accuracy (&gt;= 16.5% assignment floor). Student v2 achieves <b>40.0%</b> full-frame accuracy via improved date extraction (60.0% vs 46.0%), but drops to <b>94.0%</b> JSON validity, failing the quality gate. Hence, v1 is selected for production.", body_style))
    story.append(Spacer(1, 2))

    # ─────────────────────────────────────────────────────────────────────────────
    # TASK 3
    # ─────────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("3. Task 3: The Inference Service in a Container", h1_style))
    story.append(Paragraph("<b>Service Architecture:</b> Implemented in <code>service/app.py</code> with FastAPI and Uvicorn. Exposes three core endpoints: (1) <code>POST /parse</code> parsing natural language commands into 4-key JSON with response headers <code>X-Model-Version</code> and <code>X-Served-By</code>; (2) <code>GET /healthz</code> returning HTTP 200 for liveness; (3) <code>GET /readyz</code> returning HTTP 503 during model download and HTTP 200 once weights are fully loaded into memory.", body_style))
    story.append(Paragraph("<b>Externalized Weight Retrieval &amp; Secret Ingestion:</b> Image layers strictly exclude model weights. On startup, the service queries S3 using Boto3 configured with environment variables (<code>MODEL_URI</code>, <code>MODEL_VERSION</code>, <code>S3_ENDPOINT</code>, <code>MAX_NEW_TOKENS</code>) and credentials populated exclusively from a Kubernetes Secret (<code>s3-credentials</code>).", body_style))
    story.append(Paragraph("<b>Schema Validation &amp; Fault Injection:</b> Generated outputs are validated against <code>cloud_assignment/data/schema.json</code>. Malformed JSON or schema deviations trigger HTTP 500 with <code>{\"error\": \"invalid_model_output\"}</code>. With <code>FAULT_INJECT=1</code>, model output is overridden with <code>\"not json\"</code>, validating fail-safe error handling.", body_style))
    story.append(Paragraph("<b>Container Optimization &amp; 50-Request Benchmark:</b> Built via multi-stage Dockerfile utilizing CPU-only PyTorch (<code>torch==2.6.0+cpu</code>), stripping CUDA/cuDNN binaries. Final image disk footprint is <b>1.64 GB</b> (under the 2.0 GB ceiling). Running 50 sequential requests under cgroup limits of 1 vCPU and 1 GiB memory yielded a measured peak memory of <b>333.9 MiB (0.326 GiB)</b> with zero OOM events. 48 requests returned HTTP 200; 2 requests returned HTTP 500 because raw model outputs contained syntax errors caught by the schema validator, demonstrating active error protection.", body_style))
    story.append(Spacer(1, 2))

    # ─────────────────────────────────────────────────────────────────────────────
    # TASK 4
    # ─────────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("4. Task 4: Kubernetes Deployment, Scaling, and Reliability", h1_style))
    story.append(Paragraph("<b>Cluster Topology &amp; Ingress Routing:</b> Deployed to namespace <code>app</code> on k3d Kubernetes. Ingress routing maps port 8080 traffic to the ClusterIP Service on port 80, forwarding to pod port 8000. Traefik handles Layer 7 routing and round-robin load distribution.", body_style))
    story.append(Paragraph("<b>Horizontal Pod Autoscaling (HPA):</b> Configured with min 1, max 2 replicas, target CPU utilization 70%. Under load, metrics-server registered high CPU, automatically triggering scaling from 1 to 2 replicas, and scaling back down post-cooldown.", body_style))
    story.append(Paragraph("<b>Zero-Downtime Rolling Updates &amp; Rollback:</b> During active traffic, deployment configuration was updated from <code>v1</code> to <code>v2</code> using <code>maxUnavailable: 0</code>, <code>maxSurge: 1</code>, and a container <code>preStop: [\"/bin/sleep\", \"3\"]</code> hook to allow Ingress endpoint deregistration before process exit. Under continuous Locust load, 119 requests were served across versions (50 on v1, 69 on v2) with zero connection drops (HTTP 502/503 = 0) and zero HTTP 500 failures (0.00% error rate, meeting the &lt;= 0.5% threshold). A subsequent <code>kubectl rollout undo deployment/command-parser -n app</code> successfully restored <code>X-Model-Version: v1</code> with 2 Ready replicas.", body_style))
    story.append(Paragraph("<b>Pod Recovery &amp; Cold Start:</b> Deleting an active pod during load testing resulted in immediate replica replacement, restoring 2 Ready pods in under 20 seconds with 0 connection drops. Cold-start benchmarks (measuring duration from pod creation to <code>readyz</code> HTTP 200 across 3 clean runs) recorded <b>72.58s, 9.82s, and 19.02s</b> (median: <b>19.02s</b>).", body_style))
    story.append(Paragraph("<b>Load Balancing Distribution:</b> Locust header analysis across 2 healthy replicas over 2 minutes showed Replica A served <b>51.0% (75 requests)</b> and Replica B served <b>49.0% (72 requests)</b>, comfortably satisfying the 30% balance rule.", body_style))
    story.append(Spacer(1, 2))

    # ─────────────────────────────────────────────────────────────────────────────
    # TASK 5
    # ─────────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("5. Task 5: Subnetting and Network Access Control (NACL)", h1_style))
    story.append(Paragraph("<b>Subnet Partitioning (10.20.0.0/16):</b> Allocated consecutively from largest host requirement to smallest using minimal power-of-two prefixes 2^(32-prefix) - 2 &gt;= Hosts:", body_style))

    subnet_data = [
        [Paragraph("Subnet", table_cell_header), Paragraph("Hosts Req.", table_cell_header), Paragraph("Network CIDR", table_cell_header), Paragraph("Prefix", table_cell_header), Paragraph("Usable Host Range", table_cell_header), Paragraph("Broadcast", table_cell_header), Paragraph("Usable Hosts", table_cell_header)],
        [Paragraph("app", table_cell_bold), Paragraph("1,000", table_cell), Paragraph("10.20.0.0", table_cell), Paragraph("/22", table_cell), Paragraph("10.20.0.1 – 10.20.3.254", table_cell), Paragraph("10.20.3.255", table_cell), Paragraph("1,022", table_cell)],
        [Paragraph("public", table_cell_bold), Paragraph("250", table_cell), Paragraph("10.20.4.0", table_cell), Paragraph("/24", table_cell), Paragraph("10.20.4.1 – 10.20.4.254", table_cell), Paragraph("10.20.4.255", table_cell), Paragraph("254", table_cell)],
        [Paragraph("data", table_cell_bold), Paragraph("100", table_cell), Paragraph("10.20.5.0", table_cell), Paragraph("/25", table_cell), Paragraph("10.20.5.1 – 10.20.5.126", table_cell), Paragraph("10.20.5.127", table_cell), Paragraph("126", table_cell)],
        [Paragraph("management", table_cell_bold), Paragraph("20", table_cell), Paragraph("10.20.5.128", table_cell), Paragraph("/27", table_cell), Paragraph("10.20.5.129 – 10.20.5.158", table_cell), Paragraph("10.20.5.159", table_cell), Paragraph("30", table_cell)],
    ]
    t_sub = Table(subnet_data, colWidths=[65, 45, 65, 35, 145, 70, 45])
    t_sub.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_sub)
    story.append(Spacer(1, 2))
    story.append(Paragraph("<b>Stateless NACL Theory &amp; Rule Ordering:</b> Stateless NACLs do not preserve session state; each inbound and outbound packet is evaluated independently. Return web traffic requires explicit outbound ephemeral port rules (1024–65535). Rules are evaluated in strict ascending order: rule 100 explicitly blocks abusive range <code>198.51.100.0/24</code> across all ports before rule 110/120 allows broad 0.0.0.0/0 traffic. Verified 6/6 (100%) via <code>cloud_assignment/tools/nacl_sim.py</code>.", body_style))
    story.append(Spacer(1, 2))

    # ─────────────────────────────────────────────────────────────────────────────
    # TASK 6
    # ─────────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("6. Task 6: Reproducibility, Testing, and CI/CD", h1_style))
    story.append(Paragraph("<b>One-Command Lifecycle:</b> <code>make up</code> creates the k3d cluster, provisions SeaweedFS, builds Docker images, and deploys services. <code>make down</code> safely tears down all cluster resources.", body_style))
    story.append(Paragraph("<b>GitHub Actions Pipeline (.github/workflows/ci.yml):</b> Implemented with 4 sequential stages: (1) <code>lint</code> (flake8, 0 errors/warnings); (2) <code>test</code> (28 automated pytest unit tests across 4 test suites covering cleaning, service schema, pipeline, and NACL rules, all passing); (3) <code>evaluate</code> (configured to download <code>v1.0.0</code> from GitHub Release assets, verify SHA256 checksums, generate validation predictions, and enforce <code>score.py --min-validity 95</code>); (4) <code>secret-scan</code> (Gitleaks automated scan configured with <code>if: always() && !cancelled()</code>, verified locally with 0 leaks).", body_style))
    story.append(Paragraph("<b>Quality Gate Failure Verification:</b> Quality gate failure logic was empirically verified using untrained Pythia-70M predictions (<code>results/untrained_predictions.jsonl</code>), where <code>score.py</code> correctly exited with code 1 (<code>json_validity: 0.0% &lt; 95.0%</code>). The CI workflow includes a <code>test_bad_model: true</code> dispatch parameter and a <code>failing-gate-demo</code> branch trigger to demonstrate the genuine quality-gate failure remotely upon release asset upload.", body_style))
    story.append(Spacer(1, 2))

    # ─────────────────────────────────────────────────────────────────────────────
    # TASK 7
    # ─────────────────────────────────────────────────────────────────────────────
    story.append(Paragraph("7. Task 7: Performance, Cost, and Comprehensive Review", h1_style))
    story.append(Paragraph("<b>Locust Load Test Measurements (2 minutes, 4 users):</b> Total requests: <b>151</b>, successful HTTP 200: <b>147</b>, throughput: <b>1.28 req/s</b>, median latency (p50): <b>2,500 ms</b>, 95th percentile latency (p95): <b>6,300 ms</b>. Pod resource utilization during load (<code>kubectl top pods</code>): CPU was <b>554m and 549m</b>; memory was <b>349 MiB and 362 MiB</b> (peak RAM: <b>362 MiB</b>). On this laptop hardware (Intel i5-1334U, CPU-only execution inside 1-core cgroups), 4 unthrottled concurrent users cause queueing delays that push p95 to 6,300 ms, and the 1 validation syntax anomaly (V042) cycling repeatedly yields a 2.65% HTTP 500 rate.", body_style))
    story.append(Paragraph("<b>Cost Estimation (rate_card.json):</b> Hourly cost per replica = (1 vCPU * 3.50 INR) + (1 GiB * 0.45 INR) = <b>3.95 INR/hr</b>. For 2 running replicas: <b>7.90 INR/hr</b>. Requests served per hour = 147 req / 120s * 3600s = <b>4,410 req/hr</b>. Cost per 1,000 requests = (7.90 / 4,410) * 1,000 = <b>1.79 INR</b> (or <b>2.39 INR</b> under conservative 3,300 req/hr baseline).", body_style))
    story.append(Paragraph("<b>SLO Definition &amp; Error Budget:</b> Target: <b>95.0%</b> HTTP 200 responses over 2-minute load window (151 total requests). Allowed error budget: <b>7.55 requests</b>. Actual errors observed: <b>4 requests</b> (53.0% of budget consumed, 47.0% remaining). Measured success rate: <b>97.35%</b>.", body_style))

    # 6-Component Review Table
    story.append(Paragraph("<b>Critical Review Table (6 Dimensions):</b>", h2_style))
    rev_data = [
        [Paragraph("Component / Concern", table_cell_header), Paragraph("Evidence (Measured Value)", table_cell_header), Paragraph("Limitation Identified", table_cell_header), Paragraph("Proposed Improvement", table_cell_header)],
        [Paragraph("Data &amp; Storage", table_cell_bold), Paragraph("1,888 kept records; 34 duplicates removed; 19.02s median cold start", table_cell), Paragraph("S3 object retrieval on pod startup introduces ~19s init delay", table_cell), Paragraph("Pre-warm models via local node SSD DaemonSet caching", table_cell)],
        [Paragraph("Model Quality", table_cell_bold), Paragraph("99.0% JSON validity; 27.0% full frame vs 33.0% teacher", table_cell), Paragraph("Teacher labeling errors are propagated and memorized", table_cell), Paragraph("Multi-teacher ensemble distillation with majority voting", table_cell)],
        [Paragraph("Latency &amp; Throughput", table_cell_bold), Paragraph("p50: 2,500 ms; p95: 6,300 ms; throughput: 1.28 req/s", table_cell), Paragraph("CPU token autoregression limits concurrency scaling", table_cell), Paragraph("Quantize to INT8/INT4 (ONNX/vLLM) to double throughput", table_cell)],
        [Paragraph("Resource Utilisation", table_cell_bold), Paragraph("362 MiB peak RAM; 554m peak CPU under 1 core / 1 GiB limit", table_cell), Paragraph("Static 1 GiB limit causes headroom underutilization", table_cell), Paragraph("Tune limits to 512 MiB with VPA memory recommendation", table_cell)],
        [Paragraph("Reliability &amp; Recovery", table_cell_bold), Paragraph("0 dropped connections on rolling update; &lt;20s pod recovery", table_cell), Paragraph("Single-node laptop cluster lacks multi-host fault tolerance", table_cell), Paragraph("Deploy multi-zone topology with pod anti-affinity rules", table_cell)],
        [Paragraph("Security &amp; Cost", table_cell_bold), Paragraph("1.79–2.39 INR / 1k req; 0 gitleaks detected; 6/6 NACL passed", table_cell), Paragraph("Stateless NACLs require broad ephemeral return port ranges", table_cell), Paragraph("Combine NACLs with stateful Cilium / Calico NetworkPolicies", table_cell)],
    ]
    t_rev = Table(rev_data, colWidths=[85, 105, 145, 155])
    t_rev.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_rev)
    story.append(Spacer(1, 3))

    # References
    story.append(Paragraph("<b>Key References:</b> (1) Kim &amp; Rush, 'Sequence-Level Knowledge Distillation', EMNLP 2016; (2) Bastianelli et al., 'SLURP: A Spoken Language Understanding Resource Package', EMNLP 2020; (3) Biderman et al., 'Pythia: A Suite for Analyzing Large Language Models', ICML 2023; (4) Google SRE Book, 'Service Level Objectives', O'Reilly Media; (5) Kubernetes Networking &amp; Ingress Architecture Guide.", body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report compiled successfully to {OUTPUT_PDF}")


if __name__ == "__main__":
    build_pdf()
