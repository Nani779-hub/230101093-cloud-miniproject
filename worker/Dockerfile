FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir boto3==1.39.2

COPY worker/worker.py /app/worker.py
COPY prompts/teacher_prompt.txt /app/prompts/teacher_prompt.txt
COPY data/commands_pool.jsonl /app/data/commands_pool.jsonl

CMD ["python", "worker.py"]
