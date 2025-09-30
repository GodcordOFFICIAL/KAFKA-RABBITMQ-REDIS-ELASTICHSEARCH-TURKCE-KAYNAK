# Kafka, RabbitMQ, Redis ve Elasticsearch - Makefile
# Bu Makefile tüm servisleri yönetmek için kullanılır

.PHONY: help setup start stop clean status test build deploy docs

# Default target
.DEFAULT_GOAL := help

# Project variables
PROJECT_NAME := kafka-rabbitmq-redis-elasticsearch
VERSION := 1.0.0
COMPOSE_DIR := deployment/docker-compose
EXAMPLES_DIR := examples

# Color codes for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m

# Helper function to print colored output
define print_info
	@echo -e "$(BLUE)ℹ️ $(1)$(NC)"
endef

define print_success
	@echo -e "$(GREEN)✅ $(1)$(NC)"
endef

define print_warning
	@echo -e "$(YELLOW)⚠️ $(1)$(NC)"
endef

define print_error
	@echo -e "$(RED)❌ $(1)$(NC)"
endef

help: ## Show this help message
	@echo -e "$(PURPLE)============================================$(NC)"
	@echo -e "$(PURPLE)🚀 $(PROJECT_NAME) v$(VERSION)$(NC)"
	@echo -e "$(PURPLE)============================================$(NC)"
	@echo ""
	@echo -e "$(CYAN)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo -e "$(YELLOW)Examples:$(NC)"
	@echo "  make setup          # Complete setup"
	@echo "  make start-kafka    # Start only Kafka"
	@echo "  make test-all       # Run all tests"
	@echo "  make clean          # Clean everything"

setup: ## Complete setup - check requirements and start all services
	$(call print_info,"Setting up $(PROJECT_NAME)...")
	@chmod +x setup.sh
	@./setup.sh setup
	$(call print_success,"Setup completed successfully!")

# ==============================================================================
# SERVICE MANAGEMENT
# ==============================================================================

start: start-all ## Start all services

start-all: ## Start all services (Kafka, RabbitMQ, Redis, Elasticsearch)
	$(call print_info,"Starting all services...")
	@chmod +x setup.sh
	@./setup.sh start-all

start-kafka: ## Start Kafka cluster only
	$(call print_info,"Starting Kafka cluster...")
	@cd $(COMPOSE_DIR) && docker-compose -f kafka-cluster.yml up -d
	$(call print_success,"Kafka cluster started")

start-rabbitmq: ## Start RabbitMQ only
	$(call print_info,"Starting RabbitMQ...")
	@chmod +x setup.sh
	@./setup.sh start-rabbitmq

start-redis: ## Start Redis only
	$(call print_info,"Starting Redis...")
	@chmod +x scripts/setup_redis.sh
	@./scripts/setup_redis.sh
	$(call print_success,"Redis started")

start-elasticsearch: ## Start Elasticsearch only
	$(call print_info,"Starting Elasticsearch...")
	@chmod +x scripts/setup_elasticsearch.sh
	@./scripts/setup_elasticsearch.sh
	$(call print_success,"Elasticsearch started")

stop: ## Stop all services
	$(call print_info,"Stopping all services...")
	@chmod +x setup.sh
	@./setup.sh stop
	$(call print_success,"All services stopped")

restart: stop start ## Restart all services

status: ## Show service status
	@chmod +x setup.sh
	@./setup.sh status

clean: ## Stop and remove all containers, volumes, and data
	$(call print_warning,"This will remove all data!")
	@chmod +x setup.sh
	@./setup.sh clean

# ==============================================================================
# DEVELOPMENT COMMANDS
# ==============================================================================

build: build-java build-python ## Build all examples

build-java: ## Build Java examples
	$(call print_info,"Building Java examples...")
	@cd $(EXAMPLES_DIR)/kafka/java && mvn clean compile
	$(call print_success,"Java examples built")

build-python: ## Prepare Python environment
	$(call print_info,"Setting up Python environment...")
	@cd $(EXAMPLES_DIR)/kafka/python && pip install -r requirements.txt
	$(call print_success,"Python environment ready")

# ==============================================================================
# TESTING COMMANDS
# ==============================================================================

test: test-all ## Run all tests

test-all: test-kafka test-rabbitmq test-redis test-elasticsearch ## Run tests for all services

test-kafka: ## Test Kafka functionality
	$(call print_info,"Testing Kafka...")
	@cd $(EXAMPLES_DIR)/kafka/scripts && chmod +x test_kafka.sh && ./test_kafka.sh
	$(call print_success,"Kafka tests completed")

test-rabbitmq: ## Test RabbitMQ functionality
	$(call print_info,"Testing RabbitMQ...")
	@cd $(EXAMPLES_DIR)/rabbitmq/python && python simple_producer.py & sleep 2 && python simple_consumer.py &
	$(call print_success,"RabbitMQ tests completed")

test-redis: ## Test Redis functionality
	$(call print_info,"Testing Redis...")
	@cd $(EXAMPLES_DIR)/redis/python && python basic_operations.py
	$(call print_success,"Redis tests completed")

test-elasticsearch: ## Test Elasticsearch functionality
	$(call print_info,"Testing Elasticsearch...")
	@cd $(EXAMPLES_DIR)/elasticsearch/python && python basic_operations.py
	$(call print_success,"Elasticsearch tests completed")

# Performance testing
perf-test: ## Run performance tests
	$(call print_info,"Running performance tests...")
	@cd $(EXAMPLES_DIR)/kafka/scripts && chmod +x performance_test.sh && ./performance_test.sh

# Load testing
load-test: ## Run load tests
	$(call print_info,"Running load tests...")
	@echo "Load tests will be added soon..."

# ==============================================================================
# MONITORING COMMANDS
# ==============================================================================

logs: ## Show logs for all services
	@docker-compose -f $(COMPOSE_DIR)/kafka-cluster.yml logs -f

logs-kafka: ## Show Kafka logs
	@docker logs -f kafka1

logs-rabbitmq: ## Show RabbitMQ logs
	@docker logs -f rabbitmq

logs-redis: ## Show Redis logs
	@docker logs -f redis-server

logs-elasticsearch: ## Show Elasticsearch logs
	@docker logs -f elasticsearch

logs-kibana: ## Show Kibana logs
	@docker logs -f kibana

monitor: ## Start monitoring stack (Prometheus + Grafana)
	$(call print_info,"Starting monitoring stack...")
	@cd $(COMPOSE_DIR) && docker-compose -f monitoring.yml up -d
	$(call print_success,"Monitoring stack started")
	$(call print_info,"Grafana: http://localhost:3000 (admin/grafana123)")
	$(call print_info,"Prometheus: http://localhost:9090")

# ==============================================================================
# DATA MANAGEMENT
# ==============================================================================

backup: ## Backup all data
	$(call print_info,"Creating backup...")
	@mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	@echo "Backup functionality will be added soon..."

restore: ## Restore from backup
	$(call print_warning,"Restore functionality will be added soon...")

init-data: ## Initialize with sample data
	$(call print_info,"Initializing sample data...")
	@cd $(EXAMPLES_DIR)/kafka/scripts && chmod +x init_sample_data.sh && ./init_sample_data.sh
	$(call print_success,"Sample data initialized")

# ==============================================================================
# TOPIC MANAGEMENT
# ==============================================================================

create-topics: ## Create sample topics
	$(call print_info,"Creating sample topics...")
	@docker exec kafka1 kafka-topics.sh --create --bootstrap-server localhost:9092 --topic user-events --partitions 6 --replication-factor 1 --if-not-exists
	@docker exec kafka1 kafka-topics.sh --create --bootstrap-server localhost:9092 --topic order-events --partitions 3 --replication-factor 1 --if-not-exists
	@docker exec kafka1 kafka-topics.sh --create --bootstrap-server localhost:9092 --topic system-logs --partitions 1 --replication-factor 1 --if-not-exists
	$(call print_success,"Sample topics created")

list-topics: ## List all Kafka topics
	@docker exec kafka1 kafka-topics.sh --list --bootstrap-server localhost:9092

describe-topics: ## Describe all Kafka topics
	@docker exec kafka1 kafka-topics.sh --describe --bootstrap-server localhost:9092

# ==============================================================================
# EXAMPLES
# ==============================================================================

run-producer: ## Run sample producer
	$(call print_info,"Running sample producer...")
	@cd $(EXAMPLES_DIR)/kafka/python && python simple_producer.py

run-consumer: ## Run sample consumer
	$(call print_info,"Running sample consumer...")
	@cd $(EXAMPLES_DIR)/kafka/python && python simple_consumer.py

run-java-producer: ## Run Java producer
	$(call print_info,"Running Java producer...")
	@cd $(EXAMPLES_DIR)/kafka/java && mvn exec:java -Dexec.mainClass="SimpleProducer"

run-java-consumer: ## Run Java consumer
	$(call print_info,"Running Java consumer...")
	@cd $(EXAMPLES_DIR)/kafka/java && mvn exec:java -Dexec.mainClass="SimpleConsumer"

run-redis-demo: ## Run Redis demo
	$(call print_info,"Running Redis demo...")
	@cd $(EXAMPLES_DIR)/redis/python && python basic_operations.py

run-redis-lab: ## Run Redis user profile lab
	$(call print_info,"Running Redis user profile lab...")
	@cd $(EXAMPLES_DIR)/redis/python && python user_profile_lab.py

run-redis-pubsub: ## Run Redis Pub/Sub demo
	$(call print_info,"Running Redis Pub/Sub demo...")
	@cd $(EXAMPLES_DIR)/redis/python && python pubsub_examples.py

run-redis-chat: ## Run Redis chat application
	$(call print_info,"Running Redis chat application...")
	@echo "Usage: python chat_application.py <room_name> <username>"
	@echo "Example: python chat_application.py general alice"
	@cd $(EXAMPLES_DIR)/redis/python && python chat_application.py general demo_user

run-redis-cluster: ## Run Redis cluster management demo
	$(call print_info,"Running Redis cluster demo...")
	@cd $(EXAMPLES_DIR)/redis/python && python cluster_management.py

redis-cluster-health: ## Check Redis cluster health
	$(call print_info,"Checking Redis cluster health...")
	@redis-cli -p 7001 cluster nodes

redis-cluster-info: ## Show Redis cluster information
	$(call print_info,"Redis cluster information...")
	@redis-cli -p 7001 cluster info

run-elasticsearch-demo: ## Run Elasticsearch demo
	$(call print_info,"Running Elasticsearch demo...")
	@cd $(EXAMPLES_DIR)/elasticsearch/python && python basic_operations.py

run-product-search-lab: ## Run product search lab
	$(call print_info,"Running product search lab...")
	@cd $(EXAMPLES_DIR)/elasticsearch/python && python product_search_lab.py

run-elasticsearch-crud: ## Run Elasticsearch advanced CRUD demo
	$(call print_info,"Running Elasticsearch advanced CRUD demo...")
	@cd $(EXAMPLES_DIR)/elasticsearch/python && python advanced_crud_operations.py

run-elasticsearch-search: ## Run Elasticsearch search queries demo
	$(call print_info,"Running Elasticsearch search queries demo...")
	@cd $(EXAMPLES_DIR)/elasticsearch/python && python advanced_search_queries.py

run-elasticsearch-aggregations: ## Run Elasticsearch aggregations demo
	$(call print_info,"Running Elasticsearch aggregations demo...")
	@cd $(EXAMPLES_DIR)/elasticsearch/python && python advanced_aggregations.py

elasticsearch-health: ## Check Elasticsearch cluster health
	$(call print_info,"Checking Elasticsearch cluster health...")
	@curl -s "http://localhost:9200/_cluster/health?pretty"

elasticsearch-indices: ## List Elasticsearch indices
	$(call print_info,"Listing Elasticsearch indices...")
	@curl -s "http://localhost:9200/_cat/indices?v"

elasticsearch-nodes: ## Check Elasticsearch nodes
	$(call print_info,"Checking Elasticsearch nodes...")
	@curl -s "http://localhost:9200/_cat/nodes?v"

## Integration Examples
run-integration-demo: ## Run complete integration platform demo
	$(call print_info,"Running event-driven e-commerce integration demo...")
	@cd $(EXAMPLES_DIR)/integration/python && python ecommerce_platform.py

start-monitoring-dashboard: ## Start comprehensive monitoring dashboard
	$(call print_info,"Starting comprehensive monitoring dashboard...")
	@cd $(EXAMPLES_DIR)/integration/python && python monitoring_dashboard.py

run-performance-benchmark: ## Run performance benchmark suite
	$(call print_info,"Running performance benchmark suite...")
	@cd $(EXAMPLES_DIR)/integration/python && python -c "from monitoring_dashboard import PerformanceBenchmarkSuite; suite = PerformanceBenchmarkSuite(); suite.run_full_benchmark()"

optimize-performance: ## Run automated performance optimization
	$(call print_info,"Running automated performance optimization...")
	@cd $(EXAMPLES_DIR)/integration/python && python -c "from monitoring_dashboard import AutomatedPerformanceOptimizer, IntegratedPerformanceMonitor; monitor = IntegratedPerformanceMonitor(); optimizer = AutomatedPerformanceOptimizer(monitor); result = optimizer.run_optimization_cycle(); print('Optimization completed!')"

integration-status: ## Check integration platform status
	$(call print_info,"Checking technology availability...")
	@cd $(EXAMPLES_DIR)/integration/python && python -c "from ecommerce_platform import TechnologyChecker; tech = TechnologyChecker.get_available_technologies(); [print(f'   {\'\u2705\' if available else \'\u274c\'} {name.upper()}: {\'Available\' if available else \'Not available\'}') for name, available in tech.items()]; print(f'\n📊 Available: {sum(tech.values())}/4 technologies')"

# ==============================================================================
# DOCUMENTATION
# ==============================================================================

docs: ## Generate documentation
	$(call print_info,"Generating documentation...")
	@echo "Documentation generation will be added soon..."

docs-serve: ## Serve documentation locally
	$(call print_info,"Serving documentation...")
	@echo "Documentation server will be added soon..."

# ==============================================================================
# ENVIRONMENT MANAGEMENT
# ==============================================================================

env-setup: ## Setup environment variables
	$(call print_info,"Setting up environment...")
	@if [ ! -f .env ]; then cp .env.example .env; $(call print_success,".env file created from template"); else $(call print_warning,".env file already exists"); fi

env-check: ## Check environment configuration
	$(call print_info,"Checking environment configuration...")
	@docker --version
	@docker-compose --version
	$(call print_success,"Environment check completed")

# ==============================================================================
# UTILITY COMMANDS
# ==============================================================================

ps: ## Show running containers
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

exec-kafka: ## Execute shell in Kafka container
	@docker exec -it kafka1 /bin/bash

exec-rabbitmq: ## Execute shell in RabbitMQ container
	@docker exec -it rabbitmq /bin/bash

exec-redis: ## Execute Redis CLI
	@docker exec -it redis-server redis-cli -a redis123

exec-elasticsearch: ## Execute shell in Elasticsearch container
	@docker exec -it elasticsearch /bin/bash

health: ## Check health of all services
	$(call print_info,"Checking service health...")
	@echo "Kafka:"
	@docker exec kafka1 kafka-broker-api-versions.sh --bootstrap-server localhost:9092 > /dev/null 2>&1 && echo "  ✅ Healthy" || echo "  ❌ Unhealthy"
	@echo "RabbitMQ:"
	@docker exec rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1 && echo "  ✅ Healthy" || echo "  ❌ Unhealthy"
	@echo "Redis:"
	@docker exec redis-server redis-cli --no-auth-warning -a redis123 ping > /dev/null 2>&1 && echo "  ✅ Healthy" || echo "  ❌ Unhealthy"
	@echo "Elasticsearch:"
	@curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1 && echo "  ✅ Healthy" || echo "  ❌ Unhealthy"

update: ## Update all Docker images
	$(call print_info,"Updating Docker images...")
	@docker-compose -f $(COMPOSE_DIR)/kafka-cluster.yml pull
	$(call print_success,"Images updated")

prune: ## Clean up unused Docker resources
	$(call print_warning,"Cleaning up unused Docker resources...")
	@docker system prune -f
	@docker volume prune -f
	$(call print_success,"Cleanup completed")

# ==============================================================================
# CI/CD COMMANDS
# ==============================================================================

ci-setup: ## Setup for CI/CD
	$(call print_info,"Setting up CI/CD environment...")
	@echo "CI/CD setup will be added soon..."

ci-test: ## Run tests in CI mode
	$(call print_info,"Running CI tests...")
	@echo "CI tests will be added soon..."

# ==============================================================================
# DEVELOPMENT HELPERS
# ==============================================================================

dev-setup: env-setup build ## Complete development setup
	$(call print_success,"Development environment ready!")

dev-start: start create-topics init-data ## Start development environment with sample data
	$(call print_success,"Development environment started with sample data!")

dev-stop: stop ## Stop development environment
	$(call print_success,"Development environment stopped!")

# ==============================================================================
# VERSION MANAGEMENT
# ==============================================================================

version: ## Show version information
	@echo -e "$(PURPLE)Project: $(PROJECT_NAME)$(NC)"
	@echo -e "$(PURPLE)Version: $(VERSION)$(NC)"
	@echo -e "$(BLUE)Docker:$(NC) $(shell docker --version)"
	@echo -e "$(BLUE)Docker Compose:$(NC) $(shell docker-compose --version)"

# ==============================================================================
# QUICK ACCESS
# ==============================================================================

quick-start: setup dev-start ## Quick start everything
	$(call print_success,"🚀 Everything is ready!")
	@echo ""
	@echo -e "$(CYAN)🔗 Quick Links:$(NC)"
	@echo "  Kafka UI:        http://localhost:8080"
	@echo "  RabbitMQ:        http://localhost:15672 (admin/admin123)"
	@echo "  Redis Commander: http://localhost:8081"
	@echo "  Elasticsearch:   http://localhost:9200"
	@echo "  Kibana:          http://localhost:5601"
	@echo ""
	@echo -e "$(YELLOW)📖 Next steps:$(NC)"
	@echo "  1. Check service status: make status"
	@echo "  2. Run examples: make run-producer"
	@echo "  3. Try Redis Pub/Sub: make run-redis-pubsub"
	@echo "  4. Try Elasticsearch CRUD: make run-elasticsearch-crud"
	@echo "  5. View documentation: open docs/README.md"

# ==============================================================================
# TROUBLESHOOTING
# ==============================================================================

troubleshoot: ## Run troubleshooting checks
	$(call print_info,"Running troubleshooting checks...")
	@echo "Docker status:"
	@docker info | grep -E "(Server Version|Storage Driver|Logging Driver|Cgroup Driver)" || true
	@echo ""
	@echo "Available resources:"
	@echo "  Memory: $(shell free -h 2>/dev/null | awk 'NR==2{print $$7}' || echo 'Unknown')"
	@echo "  Disk: $(shell df -h . | awk 'NR==2{print $$4}' || echo 'Unknown')"
	@echo ""
	@echo "Port availability:"
	@netstat -tuln | grep -E ":9092|:15672|:6379|:9200" || echo "  No conflicts detected"