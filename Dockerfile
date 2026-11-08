FROM python:3.11-slim

WORKDIR /app

COPY service/requirements.txt requirements.txt

RUN pip install --no-cache-dir --default-timeout=1000 \
    torch==2.6.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

COPY service/app.py app.py

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
