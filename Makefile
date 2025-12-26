# =====================================================
# LexFlow CRM - Makefile
# =====================================================
# Usage:
#   make help
#   make install
#   make dev
#   make test
#   make build
#   make docker-up
#   make docker-down
# =====================================================

APP_NAME=lexflow-crm
NODE_ENV?=development
PYTHON_ENV?=venv
DOCKER_COMPOSE=docker-compose

.DEFAULT_GOAL := help

# -----------------------------------------------------
# Colors
# -----------------------------------------------------
GREEN=\033[0;32m
BLUE=\033[0;34m
YELLOW=\033[1;33m
RESET=\033[0m

# -----------------------------------------------------
# Help
# -----------------------------------------------------
help:
	@echo "$(BLUE)LexFlow CRM Makefile Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Setup & Development$(RESET)"
	@echo "  make install        Install all dependencies"
	@echo "  make dev            Start local development servers"
	@echo "  make clean          Remove build artifacts"
	@echo ""
	@echo "$(GREEN)Testing & Quality$(RESET)"
	@echo "  make test           Run all tests"
	@echo "  make lint           Run linters"
	@echo ""
	@echo "$(GREEN)Build & Deploy$(RESET)"
	@echo "  make build          Build production assets"
	@echo "  make start          Start production server"
	@echo ""
	@echo "$(GREEN)Docker$(RESET)"
	@echo "  make docker-build   Build Docker images"
	@echo "  make docker-up      Start Docker containers"
	@echo "  make docker-down    Stop Docker containers"

# -----------------------------------------------------
# Install Dependencies
# -----------------------------------------------------
install:
	@echo "$(YELLOW)Installing Node dependencies...$(RESET)"
	npm install
	@if [ -f requirements.txt ]; then \
		echo "$(YELLOW)Installing Python dependencies...$(RESET)"; \
		python3 -m venv $(PYTHON_ENV); \
		. $(PYTHON_ENV)/bin/activate && pip install -r requirements.txt; \
	fi

# -----------------------------------------------------
# Development
# -----------------------------------------------------
dev:
	@echo "$(GREEN)Starting LexFlow CRM in development mode...$(RESET)"
	NODE_ENV=$(NODE_ENV) npm run dev

# -----------------------------------------------------
# Testing & Linting
# -----------------------------------------------------
test:
	@echo "$(GREEN)Running tests...$(RESET)"
	npm test
	@if [ -f pytest.ini ]; then \
		. $(PYTHON_ENV)/bin/activate && pytest; \
	fi

lint:
	@echo "$(GREEN)Running linters...$(RESET)"
	npm run lint
	@if [ -f .flake8 ]; then \
		. $(PYTHON_ENV)/bin/activate && flake8; \
	fi

# -----------------------------------------------------
# Build & Production
# -----------------------------------------------------
build:
	@echo "$(GREEN)Building production assets...$(RESET)"
	npm run build

start:
	@echo "$(GREEN)Starting LexFlow CRM (production)...$(RESET)"
	NODE_ENV=production npm start

# -----------------------------------------------------
# Cleanup
# -----------------------------------------------------
clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(RESET)"
	rm -rf node_modules dist build
	rm -rf $(PYTHON_ENV)

# -----------------------------------------------------
# Docker
# -----------------------------------------------------
docker-build:
	@echo "$(GREEN)Building Docker images...$(RESET)"
	$(DOCKER_COMPOSE) build

docker-up:
	@echo "$(GREEN)Starting Docker containers...$(RESET)"
	$(DOCKER_COMPOSE) up -d

docker-down:
	@echo "$(YELLOW)Stopping Docker containers...$(RESET)"
	$(DOCKER_COMPOSE) down
