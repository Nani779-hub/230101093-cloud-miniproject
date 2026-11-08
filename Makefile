.PHONY: help setup up down lint test train evaluate nacl-check docker-build clean

ifeq ($(OS),Windows_NT)
    PYTHON ?= $(if $(wildcard .venv/Scripts/python.exe),.venv\Scripts\python.exe,python)
    FLAKE8 ?= $(if $(wildcard .venv/Scripts/flake8.exe),.venv\Scripts\flake8.exe,flake8)
else
    PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
    FLAKE8 ?= $(if $(wildcard .venv/bin/flake8),.venv/bin/flake8,flake8)
endif

K3D_CLUSTER_NAME ?= command-parser
IMAGE_NAME ?= command-parser-service:latest
SUBSET ?= 1500
GOLD ?= cloud_assignment/data/validation.jsonl

help:
	@echo "========================================================================"
	@echo "Cloud Computing Mini Project - Roll No: 230101093"
	@echo "========================================================================"
	@echo "Available make targets:"
	@echo "  setup         - Validate python, docker, kubectl prerequisites"
	@echo "  up            - Provision cluster, SeaweedFS, S3 buckets, and deploy"
	@echo "  down          - Delete Kubernetes resources and tear down k3d cluster"
	@echo "  lint          - Run Flake8 linter on python code"
	@echo "  test          - Execute automated test suite in tests/"
	@echo "  train         - Fine-tune Pythia-70M student model (use SUBSET=50 for quick test)"
	@echo "  evaluate      - Run evaluation suite comparing teacher, untrained and trained student"
	@echo "  nacl-check    - Test simulated stateless NACL rules against sample packets"
	@echo "  docker-build  - Build reproducible Docker image for the parsing microservice"
	@echo "  clean         - Remove Python caches, build artifacts, and test temp files"
	@echo "========================================================================"

setup:
	@$(PYTHON) --version
	@docker --version
	@kubectl version --client

up:
	@echo "Step 1: Creating k3d cluster..."
	k3d cluster create --config cluster/k3d.yaml
	@echo "Step 2: Deploying storage, namespaces and secrets..."
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/secret.yaml
	kubectl apply -f storage/seaweedfs.yaml
	kubectl wait --for=condition=ready pod -l app=seaweedfs -n data --timeout=120s
	kubectl exec -n data deploy/seaweedfs -- wget -q --method=PUT http://127.0.0.1:8333/datasets -O -
	kubectl exec -n data deploy/seaweedfs -- wget -q --method=PUT http://127.0.0.1:8333/models -O -
	@echo "Step 3: Building and deploying application..."
	docker build -t $(IMAGE_NAME) -f Dockerfile .
	k3d image import $(IMAGE_NAME) -c $(K3D_CLUSTER_NAME)
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/ingress.yaml
	kubectl apply -f k8s/networkpolicy.yaml
	kubectl apply -f k8s/hpa.yaml
	kubectl rollout status deployment/command-parser -n app --timeout=180s
	@echo "Deployment complete. Application is available at http://localhost:8080"

down:
	@echo "Tearing down Kubernetes resources and deleting cluster..."
	-kubectl delete -f k8s/hpa.yaml --ignore-not-found=true
	-kubectl delete -f k8s/networkpolicy.yaml --ignore-not-found=true
	-kubectl delete -f k8s/ingress.yaml --ignore-not-found=true
	-kubectl delete -f k8s/service.yaml --ignore-not-found=true
	-kubectl delete -f k8s/deployment.yaml --ignore-not-found=true
	-kubectl delete -f storage/seaweedfs.yaml --ignore-not-found=true
	-kubectl delete -f k8s/secret.yaml --ignore-not-found=true
	-kubectl delete -f k8s/namespace.yaml --ignore-not-found=true
	-k3d cluster delete $(K3D_CLUSTER_NAME)
	@echo "Cluster teardown complete."

lint:
	@echo "Running Flake8 linter..."
	$(FLAKE8) --max-line-length=120 --ignore=E402,E501,W503 worker service tests training evaluation

test:
	@echo "Running test suite..."
	$(PYTHON) -m pytest tests/test_cleaning_rules.py tests/test_service_schema.py tests/test_nacl_rules.py -v

train:
	@echo "Fine-tuning Pythia-70M student model (SUBSET=$(SUBSET))..."
	$(PYTHON) training/train.py --subset $(SUBSET)

evaluate:
	@echo "Running evaluation suite across teacher, untrained and trained models..."
	$(PYTHON) evaluation/evaluate.py --min-validity 95

nacl-check:
	$(PYTHON) cloud_assignment/tools/nacl_sim.py network/nacl.json cloud_assignment/network/packets_sample.jsonl --check

docker-build:
	docker build -t $(IMAGE_NAME) -f Dockerfile .

clean:
	@$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink() for p in pathlib.Path('.').rglob('*.py[cod]') if p.is_file()]; shutil.rmtree('.pytest_cache', ignore_errors=True); shutil.rmtree('build', ignore_errors=True); shutil.rmtree('dist', ignore_errors=True)"
	@echo "Clean completed successfully."
