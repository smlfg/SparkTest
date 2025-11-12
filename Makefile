# Makefile for SparkTest
# Convenient shortcuts for common operations

.PHONY: help deploy start stop restart status logs clean test test-smoke test-integration benchmark format lint install-dev

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)SparkTest - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

## Deployment Commands

deploy: ## Deploy the entire SparkTest platform
	@echo "$(BLUE)Deploying SparkTest...$(NC)"
	./agent10_deploy.sh

deploy-clean: ## Clean deploy (removes existing containers and volumes)
	@echo "$(YELLOW)Cleaning and deploying...$(NC)"
	./agent10_deploy.sh --clean

start: ## Start all services
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started$(NC)"

stop: ## Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose stop
	@echo "$(GREEN)Services stopped$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	docker-compose restart
	@echo "$(GREEN)Services restarted$(NC)"

down: ## Stop and remove all containers
	@echo "$(YELLOW)Stopping and removing containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)Containers removed$(NC)"

clean: ## Remove all containers, volumes, and generated files
	@echo "$(YELLOW)Cleaning up...$(NC)"
	docker-compose down -v
	rm -rf reports/* spark/logs/*
	@echo "$(GREEN)Cleanup complete$(NC)"

## Service Management

status: ## Show service status
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose ps

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show API Gateway logs
	docker-compose logs -f api-gateway

logs-spark: ## Show Spark Master logs
	docker-compose logs -f spark-master

logs-test: ## Show test runner logs
	docker-compose logs -f test-runner

## Testing Commands

test: ## Run all integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	./run_integration_tests.sh

test-smoke: ## Run smoke tests only
	@echo "$(BLUE)Running smoke tests...$(NC)"
	./run_integration_tests.sh smoke

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	./run_integration_tests.sh integration

test-agent: ## Run tests for specific agent (usage: make test-agent AGENT=1)
	@echo "$(BLUE)Running Agent $(AGENT) tests...$(NC)"
	./run_integration_tests.sh agent $(AGENT)

test-agents: ## Run tests for all agents
	@echo "$(BLUE)Running all agent tests...$(NC)"
	./run_integration_tests.sh agents

test-coverage: ## Generate coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	./run_integration_tests.sh coverage

## Benchmarking Commands

benchmark: ## Run all performance benchmarks
	@echo "$(BLUE)Running benchmarks...$(NC)"
	./benchmark_suite.sh

benchmark-api: ## Run API benchmarks
	@echo "$(BLUE)Running API benchmarks...$(NC)"
	./benchmark_suite.sh api

benchmark-spark: ## Run Spark benchmarks
	@echo "$(BLUE)Running Spark benchmarks...$(NC)"
	./benchmark_suite.sh spark

benchmark-redis: ## Run Redis benchmarks
	@echo "$(BLUE)Running Redis benchmarks...$(NC)"
	./benchmark_suite.sh redis

benchmark-db: ## Run database benchmarks
	@echo "$(BLUE)Running database benchmarks...$(NC)"
	./benchmark_suite.sh database

## Development Commands

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	black .
	isort .
	@echo "$(GREEN)Code formatted$(NC)"

lint: ## Run linting checks
	@echo "$(BLUE)Running linting...$(NC)"
	flake8 services/ tests/ --max-line-length=120 --extend-ignore=E203,W503
	@echo "$(GREEN)Linting complete$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checker...$(NC)"
	mypy services/ --ignore-missing-imports

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	pip install -r requirements.test.txt
	pip install flake8 black isort mypy
	@echo "$(GREEN)Dependencies installed$(NC)"

## Database Commands

db-shell: ## Open PostgreSQL shell
	@echo "$(BLUE)Opening database shell...$(NC)"
	docker-compose exec postgres psql -U sparktest -d sparktest_db

db-backup: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	mkdir -p database/backups
	docker-compose exec postgres pg_dump -U sparktest sparktest_db > database/backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup complete$(NC)"

db-restore: ## Restore database from latest backup (usage: make db-restore FILE=backup.sql)
	@echo "$(BLUE)Restoring database...$(NC)"
	docker-compose exec -T postgres psql -U sparktest sparktest_db < $(FILE)
	@echo "$(GREEN)Restore complete$(NC)"

## Monitoring Commands

metrics: ## View Prometheus metrics
	@curl -s http://localhost:8000/metrics

health: ## Check service health
	@echo "$(BLUE)Checking service health...$(NC)"
	@curl -s http://localhost:8000/health | python -m json.tool

open-spark: ## Open Spark UI in browser
	@echo "$(BLUE)Opening Spark UI...$(NC)"
	@open http://localhost:8080 || xdg-open http://localhost:8080 || echo "Open http://localhost:8080 in your browser"

open-grafana: ## Open Grafana in browser
	@echo "$(BLUE)Opening Grafana...$(NC)"
	@open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Open http://localhost:3000 in your browser"

open-api: ## Open API documentation in browser
	@echo "$(BLUE)Opening API docs...$(NC)"
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Open http://localhost:8000/docs in your browser"

## Build Commands

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)Build complete$(NC)"

build-no-cache: ## Build Docker images without cache
	@echo "$(BLUE)Building Docker images (no cache)...$(NC)"
	docker-compose build --no-cache
	@echo "$(GREEN)Build complete$(NC)"

pull: ## Pull latest Docker images
	@echo "$(BLUE)Pulling Docker images...$(NC)"
	docker-compose pull
	@echo "$(GREEN)Pull complete$(NC)"

## Utility Commands

shell-api: ## Open shell in API Gateway container
	docker-compose exec api-gateway /bin/bash

shell-test: ## Open shell in test runner container
	docker-compose exec test-runner /bin/bash

shell-spark: ## Open shell in Spark Master container
	docker-compose exec spark-master /bin/bash

ps: ## Show running containers
	@docker-compose ps

top: ## Show resource usage of containers
	@docker stats --no-stream $$(docker-compose ps -q)

inspect: ## Show detailed container information (usage: make inspect SERVICE=api-gateway)
	@docker-compose exec $(SERVICE) env

## Git Commands

git-status: ## Show git status
	@git status

git-log: ## Show git log
	@git log --oneline --graph --decorate -10

## Quick Actions

quick-test: deploy test-smoke ## Deploy and run smoke tests
	@echo "$(GREEN)Quick test complete$(NC)"

full-check: format lint test benchmark ## Run full check (format, lint, test, benchmark)
	@echo "$(GREEN)Full check complete$(NC)"

dev-setup: install-dev deploy ## Set up development environment
	@echo "$(GREEN)Development environment ready$(NC)"

reset: clean deploy ## Reset everything (clean and redeploy)
	@echo "$(GREEN)Reset complete$(NC)"
