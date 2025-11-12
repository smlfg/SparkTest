.PHONY: help install test test-unit test-integration build up down logs clean format lint type-check health

# Default target
help:
	@echo "DGX Spark Playbooks - Make Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install Python dependencies"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make build            Build all Docker images"
	@echo "  make up               Start all agents"
	@echo "  make down             Stop all agents"
	@echo "  make logs             View logs from all agents"
	@echo "  make restart          Restart all agents"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make health           Check health of all agents"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           Format code with black and isort"
	@echo "  make lint             Lint code with flake8"
	@echo "  make type-check       Type check with mypy"
	@echo "  make qa               Run all quality checks"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Clean up generated files"
	@echo "  make clean-docker     Remove all containers and images"

# Setup
install:
	pip install -r requirements.txt

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart: down up

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v -m integration

test-coverage:
	pytest tests/ --cov=shared --cov-report=html --cov-report=term

# Health checks
health:
	@echo "Checking health of all agents..."
	@for port in 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010; do \
		status=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$$port/health 2>/dev/null || echo "000"); \
		if [ "$$status" = "200" ]; then \
			echo "✓ Port $$port: Healthy"; \
		else \
			echo "✗ Port $$port: Unhealthy ($$status)"; \
		fi; \
	done

# Code quality
format:
	black shared/ agents/ tests/
	isort shared/ agents/ tests/

lint:
	flake8 shared/ agents/ tests/ --max-line-length=100 --ignore=E203,W503

type-check:
	mypy shared/ --ignore-missing-imports

qa: format lint type-check
	@echo "All quality checks passed!"

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -f generate_agent_templates.py

clean-docker:
	docker-compose down -v --rmi all

# Individual agent commands
agent1:
	docker-compose up agent1_infra

agent2:
	docker-compose up agent2_dashboard

agent3:
	docker-compose up agent3_compute

agent4:
	docker-compose up agent4_storage

agent5:
	docker-compose up agent5_networking

agent6:
	docker-compose up agent6_monitoring

agent7:
	docker-compose up agent7_security

agent8:
	docker-compose up agent8_analytics

agent9:
	docker-compose up agent9_orchestration

agent10:
	docker-compose up agent10_integration

# Build individual agents
build-agent1:
	docker-compose build agent1_infra

build-agent2:
	docker-compose build agent2_dashboard

build-agent3:
	docker-compose build agent3_compute

build-agent4:
	docker-compose build agent4_storage

build-agent5:
	docker-compose build agent5_networking

build-agent6:
	docker-compose build agent6_monitoring

build-agent7:
	docker-compose build agent7_security

build-agent8:
	docker-compose build agent8_analytics

build-agent9:
	docker-compose build agent9_orchestration

build-agent10:
	docker-compose build agent10_integration

# Development
dev:
	@echo "Starting development environment..."
	docker-compose up

dev-rebuild:
	docker-compose up --build

# GPU check
gpu-check:
	@echo "Checking GPU availability..."
	@nvidia-smi || echo "NVIDIA GPU not available"
	@echo ""
	@echo "Checking NVIDIA Container Toolkit..."
	@nvidia-container-cli info || echo "NVIDIA Container Toolkit not available"

# Generate documentation
docs:
	@echo "Generating documentation..."
	@echo "TODO: Add documentation generation"

# Show container stats
stats:
	docker stats --no-stream

# Show network info
network:
	docker network inspect spark_network
