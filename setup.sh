#!/bin/bash

# Kafka, RabbitMQ, Redis ve Elasticsearch - Quick Setup Script
# Bu script tüm servisleri hızlı bir şekilde kurmanızı sağlar

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project info
PROJECT_NAME="Kafka-RabbitMQ-Redis-Elasticsearch Learning Platform"
VERSION="1.0.0"

# Function to print colored output
print_header() {
    echo -e "${PURPLE}============================================${NC}"
    echo -e "${PURPLE}🚀 $1${NC}"
    echo -e "${PURPLE}============================================${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "${CYAN}📋 $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    print_header "Checking System Requirements"
    
    local requirements_met=true
    
    # Check Docker
    if command_exists docker; then
        print_success "Docker is installed"
        docker --version
    else
        print_error "Docker is not installed"
        print_info "Please install Docker from: https://docs.docker.com/get-docker/"
        requirements_met=false
    fi
    
    # Check Docker Compose
    if command_exists docker-compose; then
        print_success "Docker Compose is installed"
        docker-compose --version
    else
        print_error "Docker Compose is not installed"
        print_info "Please install Docker Compose from: https://docs.docker.com/compose/install/"
        requirements_met=false
    fi
    
    # Check available memory
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        local available_memory=$(free -g | awk 'NR==2{print $7}')
        if [ "$available_memory" -lt 4 ]; then
            print_warning "Available memory: ${available_memory}GB (Recommended: 4GB+)"
        else
            print_success "Available memory: ${available_memory}GB"
        fi
    fi
    
    # Check available disk space
    if command_exists df; then
        local available_space=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
        if [ "$available_space" -lt 10 ]; then
            print_warning "Available disk space: ${available_space}GB (Recommended: 10GB+)"
        else
            print_success "Available disk space: ${available_space}GB"
        fi
    fi
    
    if [ "$requirements_met" = false ]; then
        print_error "System requirements not met. Please install missing components."
        exit 1
    fi
    
    print_success "All system requirements are satisfied!"
    echo ""
}

# Setup project structure
setup_project_structure() {
    print_header "Setting up Project Structure"
    
    print_step "Creating directories..."
    
    # Main directories
    mkdir -p logs/{kafka,rabbitmq,redis,elasticsearch}
    mkdir -p data/{kafka,rabbitmq,redis,elasticsearch}
    mkdir -p config/{kafka,rabbitmq,redis,elasticsearch}
    mkdir -p scripts
    
    print_success "Project structure created"
    
    # Make scripts executable
    if [ -d "examples/kafka/scripts" ]; then
        chmod +x examples/kafka/scripts/*.sh
        print_success "Kafka scripts made executable"
    fi
    
    echo ""
}

# Start Kafka cluster
start_kafka() {
    print_header "Starting Kafka Cluster"
    
    cd deployment/docker-compose
    
    print_step "Starting Zookeeper and Kafka..."
    docker-compose -f kafka-cluster.yml up -d
    
    print_step "Waiting for Kafka to be ready..."
    sleep 30
    
    # Health check
    if docker exec kafka1 kafka-broker-api-versions.sh --bootstrap-server localhost:9092 &>/dev/null; then
        print_success "Kafka cluster is running and healthy"
        
        # Create sample topics
        print_step "Creating sample topics..."
        docker exec kafka1 kafka-topics.sh \
            --create --bootstrap-server localhost:9092 \
            --topic quickstart-events --partitions 3 --replication-factor 1 \
            --if-not-exists
        
        docker exec kafka1 kafka-topics.sh \
            --create --bootstrap-server localhost:9092 \
            --topic user-events --partitions 6 --replication-factor 1 \
            --if-not-exists
        
        print_success "Sample topics created"
    else
        print_error "Kafka cluster failed to start properly"
        return 1
    fi
    
    cd - > /dev/null
    echo ""
}

# Start RabbitMQ
start_rabbitmq() {
    print_header "Starting RabbitMQ"
    
    cd deployment/docker-compose
    
    print_step "Starting RabbitMQ..."
    cat > rabbitmq-cluster.yml << 'EOF'
version: '3.8'

services:
  rabbitmq:
    image: rabbitmq:3.12-management
    hostname: rabbitmq
    container_name: rabbitmq
    ports:
      - "5672:5672"     # AMQP port
      - "15672:15672"   # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: admin123
      RABBITMQ_DEFAULT_VHOST: /
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  rabbitmq-data:
EOF
    
    docker-compose -f rabbitmq-cluster.yml up -d
    
    print_step "Waiting for RabbitMQ to be ready..."
    sleep 20
    
    # Health check
    if docker exec rabbitmq rabbitmq-diagnostics ping &>/dev/null; then
        print_success "RabbitMQ is running and healthy"
        print_info "Management UI: http://localhost:15672 (admin/admin123)"
    else
        print_error "RabbitMQ failed to start properly"
        return 1
    fi
    
    cd - > /dev/null
    echo ""
}

# Start Redis
start_redis() {
    print_header "Starting Redis"
    
    cd deployment/docker-compose
    
    print_step "Starting Redis..."
    cat > redis-cluster.yml << 'EOF'
version: '3.8'

services:
  redis:
    image: redis:7.2-alpine
    hostname: redis
    container_name: redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass redis123
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "redis123", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis-commander:
    image: rediscommander/redis-commander:latest
    hostname: redis-commander
    container_name: redis-commander
    depends_on:
      - redis
    ports:
      - "8081:8081"
    environment:
      REDIS_HOSTS: local:redis:6379:0:redis123

volumes:
  redis-data:
EOF
    
    docker-compose -f redis-cluster.yml up -d
    
    print_step "Waiting for Redis to be ready..."
    sleep 10
    
    # Health check
    if docker exec redis redis-cli --no-auth-warning -a redis123 ping | grep -q PONG; then
        print_success "Redis is running and healthy"
        print_info "Redis Commander UI: http://localhost:8081"
    else
        print_error "Redis failed to start properly"
        return 1
    fi
    
    cd - > /dev/null
    echo ""
}

# Start Elasticsearch
start_elasticsearch() {
    print_header "Starting Elasticsearch"
    
    cd deployment/docker-compose
    
    print_step "Starting Elasticsearch..."
    cat > elasticsearch-cluster.yml << 'EOF'
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    hostname: elasticsearch
    container_name: elasticsearch
    ports:
      - "9200:9200"
      - "9300:9300"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    hostname: kibana
    container_name: kibana
    depends_on:
      - elasticsearch
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200

volumes:
  elasticsearch-data:
EOF
    
    docker-compose -f elasticsearch-cluster.yml up -d
    
    print_step "Waiting for Elasticsearch to be ready..."
    sleep 45
    
    # Health check
    if curl -s http://localhost:9200/_cluster/health | grep -q "yellow\|green"; then
        print_success "Elasticsearch is running and healthy"
        print_info "Elasticsearch: http://localhost:9200"
        print_info "Kibana: http://localhost:5601"
    else
        print_error "Elasticsearch failed to start properly"
        return 1
    fi
    
    cd - > /dev/null
    echo ""
}

# Show service status
show_status() {
    print_header "Service Status Overview"
    
    echo ""
    print_step "Checking service health..."
    
    # Kafka
    if docker exec kafka1 kafka-broker-api-versions.sh --bootstrap-server localhost:9092 &>/dev/null; then
        print_success "Kafka: Running (localhost:9092)"
        print_info "  Kafka UI: http://localhost:8080"
    else
        print_error "Kafka: Not running"
    fi
    
    # RabbitMQ
    if docker exec rabbitmq rabbitmq-diagnostics ping &>/dev/null; then
        print_success "RabbitMQ: Running (localhost:5672)"
        print_info "  Management UI: http://localhost:15672"
    else
        print_error "RabbitMQ: Not running"
    fi
    
    # Redis
    if docker exec redis redis-cli --no-auth-warning -a redis123 ping | grep -q PONG 2>/dev/null; then
        print_success "Redis: Running (localhost:6379)"
        print_info "  Redis Commander: http://localhost:8081"
    else
        print_error "Redis: Not running"
    fi
    
    # Elasticsearch
    if curl -s http://localhost:9200/_cluster/health | grep -q "yellow\|green" 2>/dev/null; then
        print_success "Elasticsearch: Running (localhost:9200)"
        print_info "  Kibana: http://localhost:5601"
    else
        print_error "Elasticsearch: Not running"
    fi
    
    echo ""
    print_header "Quick Start Commands"
    echo ""
    print_info "Kafka:"
    echo "  # List topics"
    echo "  docker exec kafka1 kafka-topics.sh --list --bootstrap-server localhost:9092"
    echo ""
    print_info "RabbitMQ:"
    echo "  # Management UI: http://localhost:15672 (admin/admin123)"
    echo ""
    print_info "Redis:"
    echo "  # Connect to Redis CLI"
    echo "  docker exec -it redis redis-cli -a redis123"
    echo ""
    print_info "Elasticsearch:"
    echo "  # Check cluster health"
    echo "  curl http://localhost:9200/_cluster/health"
    echo ""
}

# Stop all services
stop_all() {
    print_header "Stopping All Services"
    
    cd deployment/docker-compose
    
    print_step "Stopping services..."
    docker-compose -f kafka-cluster.yml down 2>/dev/null || true
    docker-compose -f rabbitmq-cluster.yml down 2>/dev/null || true
    docker-compose -f redis-cluster.yml down 2>/dev/null || true
    docker-compose -f elasticsearch-cluster.yml down 2>/dev/null || true
    
    print_success "All services stopped"
    
    cd - > /dev/null
    echo ""
}

# Clean all data
clean_all() {
    print_header "Cleaning All Data"
    
    print_warning "This will remove all containers, volumes, and data!"
    read -p "Are you sure? (y/N): " confirm
    
    if [[ $confirm == [yY] ]]; then
        cd deployment/docker-compose
        
        print_step "Removing containers and volumes..."
        docker-compose -f kafka-cluster.yml down -v 2>/dev/null || true
        docker-compose -f rabbitmq-cluster.yml down -v 2>/dev/null || true
        docker-compose -f redis-cluster.yml down -v 2>/dev/null || true
        docker-compose -f elasticsearch-cluster.yml down -v 2>/dev/null || true
        
        # Remove any orphaned containers
        docker container prune -f
        docker volume prune -f
        
        print_success "All data cleaned"
        
        cd - > /dev/null
    else
        print_info "Data cleaning cancelled"
    fi
    
    echo ""
}

# Show usage
show_help() {
    print_header "$PROJECT_NAME v$VERSION"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  setup              Complete setup (check requirements + start all services)"
    echo "  start-all          Start all services"
    echo "  start-kafka        Start only Kafka cluster"
    echo "  start-rabbitmq     Start only RabbitMQ"
    echo "  start-redis        Start only Redis"
    echo "  start-elasticsearch Start only Elasticsearch"
    echo "  status             Show service status"
    echo "  stop               Stop all services"
    echo "  clean              Stop and remove all data"
    echo "  requirements       Check system requirements"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup           # Full setup"
    echo "  $0 start-kafka     # Start only Kafka"
    echo "  $0 status          # Check service status"
    echo "  $0 clean           # Clean everything"
    echo ""
}

# Main script logic
main() {
    case "${1:-help}" in
        setup)
            check_requirements
            setup_project_structure
            start_kafka
            start_rabbitmq
            start_redis
            start_elasticsearch
            show_status
            ;;
        start-all)
            start_kafka
            start_rabbitmq
            start_redis
            start_elasticsearch
            show_status
            ;;
        start-kafka)
            start_kafka
            ;;
        start-rabbitmq)
            start_rabbitmq
            ;;
        start-redis)
            start_redis
            ;;
        start-elasticsearch)
            start_elasticsearch
            ;;
        status)
            show_status
            ;;
        stop)
            stop_all
            ;;
        clean)
            clean_all
            ;;
        requirements)
            check_requirements
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"