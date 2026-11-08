"""
Command-parsing inference service.

Endpoints:
  POST /parse     - Parse a command into intent + slots JSON
  GET  /healthz   - Liveness probe (always 200 if process is alive)
  GET  /readyz    - Readiness probe (503 until model loaded, 200 after)

Environment variables:
  MODEL_URI         - S3 key prefix for model (e.g., models/v1)
  MODEL_VERSION     - Version string (e.g., v1)
  S3_ENDPOINT       - SeaweedFS S3 endpoint
  MAX_NEW_TOKENS    - Maximum tokens to generate (default: 150)
  FAULT_INJECT      - When "1", replaces model output with "not json"
  AWS_ACCESS_KEY_ID     - S3 credentials (from K8s Secret)
  AWS_SECRET_ACCESS_KEY - S3 credentials (from K8s Secret)
"""

from contextlib import asynccontextmanager
import json
import os
import tempfile
import logging

import boto3
import torch
from fastapi import FastAPI, Response
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, StoppingCriteria, StoppingCriteriaList

# Pin single thread to prevent CPU core CFS quota throttling in containers
torch.set_num_threads(1)


class StopAtCloseBrace(StoppingCriteria):
    def __init__(self, tokenizer, prompt_len):
        self.tokenizer = tokenizer
        self.prompt_len = prompt_len

    def __call__(self, input_ids, scores, **kwargs):
        last_token = input_ids[0][-1].item()
        last_str = self.tokenizer.decode([last_token])
        if "}" in last_str:
            return True
        return False


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────────────
MODEL_URI = os.environ.get("MODEL_URI", "models/v1")
MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://seaweedfs.data.svc.cluster.local:8333")
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "150"))
FAULT_INJECT = os.environ.get("FAULT_INJECT", "0") == "1"
POD_NAME = os.environ.get("HOSTNAME", "unknown")

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "admin")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "admin")
BUCKET = os.environ.get("BUCKET", "models")

VALID_INTENTS = {
    "alarm_set", "alarm_query", "calendar_set", "calendar_query",
    "calendar_remove", "weather_query", "datetime_query", "recommendation_events",
}
REQUIRED_KEYS = {"intent", "date", "time", "place"}

# Global model state
model = None
tokenizer = None
model_ready = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    download_model()
    yield


# ── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(lifespan=lifespan)


class ParseRequest(BaseModel):
    text: str


def validate_output(output_str):
    """Validate output against schema.json rules."""
    try:
        obj = json.loads(output_str)
    except (json.JSONDecodeError, TypeError):
        return False, None

    if not isinstance(obj, dict):
        return False, None

    if set(obj.keys()) != REQUIRED_KEYS:
        return False, None

    if obj.get("intent") not in VALID_INTENTS:
        return False, None

    for slot in ("date", "time", "place"):
        val = obj.get(slot)
        if val is not None and not isinstance(val, str):
            return False, None

    return True, obj


def download_model():
    """Download model from S3 object storage."""
    global model, tokenizer, model_ready
    logger.info(f"Downloading model from S3: {BUCKET}/{MODEL_URI}")

    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="us-east-1",
    )

    # List all files in the model prefix
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=MODEL_URI.rstrip("/") + "/")
    if "Contents" not in response:
        raise RuntimeError(f"No model files found at s3://{BUCKET}/{MODEL_URI}")

    # Download to temp directory
    model_dir = os.path.join(tempfile.gettempdir(), "model")
    os.makedirs(model_dir, exist_ok=True)

    for obj in response["Contents"]:
        key = obj["Key"]
        filename = key[len(MODEL_URI.rstrip("/")) + 1:]
        if not filename or filename.endswith("/"):
            continue
        local_path = os.path.join(model_dir, filename)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        logger.info(f"  Downloading {key} -> {local_path}")
        s3.download_file(BUCKET, key, local_path)

    # Load model and tokenizer
    logger.info("Loading model into memory...")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir)
    model.eval()

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_ready = True
    logger.info(f"Model loaded successfully (version: {MODEL_VERSION})")


@app.get("/healthz")
async def healthz():
    return Response(status_code=200, content="ok")


@app.get("/readyz")
async def readyz():
    if not model_ready:
        return Response(status_code=503, content="model not loaded")
    return Response(status_code=200, content="ready")


@app.post("/parse")
def parse(request: ParseRequest):
    if not model_ready:
        return Response(
            status_code=503,
            content=json.dumps({"error": "model_not_ready"}),
            media_type="application/json",
        )

    text = request.text
    prompt = f"Command: {text}\nJSON: "

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=256)
    prompt_len = inputs["input_ids"].shape[1]
    stopping_criteria = StoppingCriteriaList([StopAtCloseBrace(tokenizer, prompt_len)])
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            stopping_criteria=stopping_criteria,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract JSON after "JSON: "
    if "JSON: " in generated:
        prediction = generated.split("JSON: ", 1)[1].strip()
    else:
        prediction = generated.strip()

    # Try to extract just the JSON object
    try:
        start = prediction.index("{")
        depth = 0
        end = start
        for j in range(start, len(prediction)):
            if prediction[j] == "{":
                depth += 1
            elif prediction[j] == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        prediction = prediction[start:end]
    except (ValueError, IndexError):
        pass

    # Fault injection
    if FAULT_INJECT:
        prediction = "not json"

    # Validate output
    valid, parsed_obj = validate_output(prediction)

    headers = {
        "X-Model-Version": MODEL_VERSION,
        "X-Served-By": POD_NAME,
    }

    if not valid:
        return Response(
            status_code=500,
            content=json.dumps({"error": "invalid_model_output"}),
            media_type="application/json",
            headers=headers,
        )

    return Response(
        status_code=200,
        content=json.dumps(parsed_obj),
        media_type="application/json",
        headers=headers,
    )
